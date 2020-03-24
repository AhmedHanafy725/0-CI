from gevent import monkey

monkey.patch_all(subprocess=False)

import json
import os
import sys
from datetime import datetime

from gevent.pywsgi import WSGIServer
from gevent import sleep
from jinja2 import Environment, FileSystemLoader, select_autoescape
from redis import Redis
from rq import Queue
from rq.job import Job
from rq_scheduler import Scheduler
from worker import conn

from actions.actions import Actions
from bcdb.bcdb import InitialConfig, ProjectRun, RepoRun, RunConfig
from beaker.middleware import SessionMiddleware
from bottle import Bottle, Response, abort, redirect, request, response, static_file
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from Jumpscale import j
from packages.vcs.vcs import VCSFactory


actions = Actions()
app = Bottle()
env = Environment(loader=FileSystemLoader("../dist"), autoescape=select_autoescape(["html", "xml"]))
q = Queue(connection=conn)
scheduler = Scheduler(connection=Redis())
r = Redis()
configs = InitialConfig()

client = j.clients.oauth_proxy.get("main")
oauth_app = j.tools.oauth_proxy.get(app, client, "/auth/login")
bot_app = j.tools.threebotlogin_proxy.get(app)
PROVIDERS = list(client.providers_list())


def trigger(repo="", branch="", commit="", committer="", id=None):
    status = "pending"
    timestamp = datetime.now().timestamp()
    if id:
        repo_run = RepoRun(id=id)
        repo_run.status = status
        repo_run.result = []
        repo_run.save()
        r.ltrim(id, -1, 0)
        r.publish(f"{repo_run.repo}_{repo_run.branch}", json.dumps({"id": id, "status": status}))
    else:
        if repo in configs.repos:
            data = {
                "timestamp": timestamp,
                "commit": commit,
                "committer": committer,
                "status": status,
                "repo": repo,
                "branch": branch,
            }
            repo_run = RepoRun(**data)
            repo_run.save()
            id = str(repo_run.id)
            data["id"] = id
            r.publish(f"{repo}_{branch}", json.dumps(data))
    if id:
        link = f"{configs.domain}/repos/{repo_run.repo.replace('/', '%2F')}/{repo_run.branch}/{str(repo_run.id)}"
        VCSObject = VCSFactory().get_cvn(repo=repo_run.repo)
        VCSObject.status_send(status=status, link=link, commit=repo_run.commit)
        job = q.enqueue_call(func=actions.build_and_test, args=(id,), result_ttl=5000, timeout=20000)
        return job
    return None


def check_configs(func):
    def wrapper(*args, **kwargs):
        if not configs.configured:
            return redirect("/api/initial_config")
        return func(*args, **kwargs)
    return wrapper


def user(func):
    @oauth_app.login_required
    def wrapper(*args, **kwargs):
        username = request.environ.get("beaker.session").get("username")
        if not (username in configs.users or (configs.admins and (not username in configs.admins))):
            return abort(401)
        return func(*args, **kwargs)
    return wrapper
        

def admin(func):
    @oauth_app.login_required
    def wrapper(*args, **kwargs):
        username = request.environ.get("beaker.session").get("username")
        if configs.admins and (not username in configs.admins):
            return abort(401)
        return func(*args, **kwargs)
    return wrapper

@app.hook("after_request")
def enable_cors_disable_cache():
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "PUT, GET, POST, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"


@app.route("/websocket/logs/<id>")
def logs(id):
    wsock = request.environ.get("wsgi.websocket")
    if not wsock:
        abort(400, "Expected WebSocket request.")

    start = 0
    while start != -1:
        length = r.llen(id)
        if start > length:
            break
        if start == length:
            sleep(1)
        result_list = r.lrange(id, start, length)
        if b"hamada ok" in result_list:
            result_list.remove(b"hamada ok")
            start = -1
        else:
            start += len(result_list)
        for result in result_list:
            try:
                wsock.send(result.decode())
            except WebSocketError:
                break


@app.route("/websocket/repos/<repo:path>/<branch>")
def update_repos_table(repo, branch):
    wsock = request.environ.get("wsgi.websocket")
    if not wsock:
        abort(400, "Expected WebSocket request.")

    sub = r.pubsub()
    sub.subscribe(f"{repo}_{branch}")
    for msg in sub.listen():
        data = msg["data"]
        if isinstance(data, bytes):
            try:
                wsock.send(msg["data"].decode())
            except WebSocketError:
                break


@app.route("/websocket/projects/<project>")
def update_projects_table(project):
    wsock = request.environ.get("wsgi.websocket")
    if not wsock:
        abort(400, "Expected WebSocket request.")

    sub = r.pubsub()
    sub.subscribe(project)
    for msg in sub.listen():
        data = msg["data"]
        if isinstance(data, bytes):
            try:
                wsock.send(msg["data"].decode())
            except WebSocketError:
                break


@app.route("/auth/login")
def login():
    provider = request.query.get("provider")

    if provider:
        if provider == "3bot":
            next_url = request.query.get("next_url")
            if next_url:
                bot_app.session["next_url"] = next_url
            return bot_app.login(request.headers["HOST"], "/auth/3bot_callback")

        redirect_url = f"https://{request.headers['HOST']}/auth/oauth_callback"
        return oauth_app.login(provider, redirect_url=redirect_url)

    return env.get_template("login.html").render(providers=PROVIDERS)


@app.route("/auth/3bot_callback")
def threebot_callback():
    bot_app.callback()


@app.route("/auth/oauth_callback")
def oauth_callback():
    user_info = oauth_app.callback()
    oauth_app.session["email"] = user_info["email"]
    return redirect(oauth_app.next_url)


@app.route("/auth/logout")
def logout():
    session = request.environ.get("beaker.session", {})
    try:
        session.invalidate()
    except AttributeError:
        pass

    redirect(request.query.get("next_url", "/"))


@app.route("/auth/authenticated")
def is_authenticated():
    session = request.environ.get("beaker.session", {})
    if session.get("authorized"):
        username = session["username"]
        email = session["email"]
        return json.dumps({"username": username, "email": email})
    return abort(403)


@app.route("/api/initial_config", method=["GET", "POST"])
@admin
def initial_config():
    """Initial configuration for the ci before start working.
    """
    confs = ["iyo_id", "iyo_secret", "domain", "chat_id", "bot_token", "vcs_host", "vcs_token", "repos"]
    conf_dict = {}
    if request.method == "GET":
        confs.extend(["configured", "admins", "users"])
        for conf in confs:
            conf_dict[conf] = getattr(configs, conf)
            conf_json = json.dumps(conf_dict)
        return conf_json
    if request.headers.get("Content-Type") == "application/json":
        for conf in confs:
            value = request.json.get(conf)
            if not value:
                return Response(f"{conf} should have a value", 400)
            if conf is "repos" and not isinstance(value, list):
                return Response("repos should be str or list", 400)
            if conf is not "repos" and not isinstance(value, str):
                return Response(f"{conf} should be str", 400)

        configs.iyo_id = request.json["iyo_id"]
        configs.iyo_secret = request.json["iyo_secret"]
        configs.domain = request.json["domain"]
        configs.chat_id = request.json["chat_id"]
        configs.bot_token = request.json["bot_token"]
        configs.vcs_host = request.json["vcs_host"]
        configs.vcs_token = request.json["vcs_token"]
        if isinstance(request.json["repos"], list):
            configs.repos = request.json["repos"]
        if not configs.admins:
            admin = request.environ.get("beaker.session").get("username")
            configs.admins.append(admin)
        configs.configured = True
        configs.save()
        sys.exit(1)


@app.route("/api/users", method=["GET", "POST", "DELETE"])
@admin
def users():
    if request.method == "GET":
        all_users = {"admins": configs.admins, "users": configs.users}
        all_json = json.dumps(all_users)
        return all_json
    if not request.headers.get("Content-Type") == "application/json":
        return abort(400)

    user = request.json.get("user")
    admin = request.json.get("admin")
    if request.method == "POST":
        if user:
            configs.users.append(user)
            configs.save()
            return Response("Added", 200)
        if admin:
            configs.admins.append(admin)
            configs.save()
            return Response("Added", 200)
    if request.method == "DELETE":
        if user and user in configs.users:
            configs.users.remove(user)
            configs.save()
            return Response("Deleted", 200)
        if admin and admin in configs.admins:
            configs.admins.remove(admin)
            configs.save()
            return Response("Deleted", 200)
    return abort(400)


@app.route("/git_trigger", method=["POST"])
@check_configs
def git_trigger():
    """Trigger the test when a post request is sent from a repo's webhook.
    """
    if request.headers.get("Content-Type") == "application/json":
        # push case
        reference = request.json.get("ref")
        if reference:
            repo = request.json["repository"]["full_name"]
            branch = reference.split("/")[-1]
            commit = request.json["after"]
            if configs.vcs_type == "github":
                committer = request.json["pusher"]["name"]
            else:
                committer = request.json["pusher"]["login"]
            branch_exist = not commit.startswith("000000")
            if branch_exist:
                job = trigger(repo=repo, branch=branch, commit=commit, committer=committer)
                if job:
                    return Response(job.get_id(), 200)
        return Response("Done", 200)
    return Response("Wrong content type", 400)


@app.route("/api/run_trigger", method=["POST", "GET"])
@user
@check_configs
def run_trigger():
    if request.method == "GET":
        redirect("/")

    if request.headers.get("Content-Type") == "application/json":
        id = request.json.get("id")
        if id:
            where = f'id="{id}" and status="pending"'
            run = RepoRun.get_objects(fields=["status"], where=where)
            if run:
                return Response(
                    f"There is a running job for this id {id}, please try again after this run finishes", 503
                )
            job = trigger(id=id)
            return Response(job.get_id(), 200)

        repo = request.json.get("repo")
        branch = request.json.get("branch")
        VCSObject = VCSFactory().get_cvn(repo=repo)
        last_commit = VCSObject.get_last_commit(branch=branch)
        committer = VCSObject.get_committer(commit=last_commit)
        where = f'repo="{repo}" and branch="{branch}" and [commit]="{last_commit}" and status="pending"'
        run = RepoRun.get_objects(fields=["status"], where=where)
        if run:
            return Response(
                f"There is a running job from this commit {last_commit}, please try again after this run finishes", 503
            )
        if last_commit:
            job = trigger(repo=repo, branch=branch, commit=last_commit, committer=committer)
        else:
            return Response(f"Couldn't get last commit from this branch {branch}, please try again", 503)
        if job:
            return Response(job.get_id(), 200)
        return Response("Wrong data", 400)


@app.route("/api/add_project", method=["POST"])
@user
@check_configs
def add_project():
    if request.headers.get("Content-Type") == "application/json":
        project_name = request.json.get("project_name")
        prequisties = request.json.get("prequisties")
        install_script = request.json.get("install_script")
        test_script = request.json.get("test_script")
        run_time = request.json.get("run_time")
        authentication = request.json.get("authentication")
        timeout = request.json.get("timeout", 3600)
        if authentication == configs.vcs_token:
            if not (
                isinstance(project_name, str)
                and isinstance(install_script, (str, list))
                and isinstance(test_script, (str, list))
                and isinstance(prequisties, (str, list))
                and isinstance(run_time, str)
                and isinstance(timeout, int)
            ):
                return Response("Wrong data", 400)

            if isinstance(install_script, list):
                install_script = " && ".join(install_script)

            if isinstance(test_script, str):
                test_script = [test_script]

            try:
                scheduler.cron(
                    cron_string=run_time,
                    func=actions.run_project,
                    args=[project_name, install_script, test_script, prequisties, timeout],
                    id=project_name,
                    timeout=timeout + 3600,
                )
            except:
                return Response("Wrong time format should be like (0 * * * *)", 400)
            return Response("Added", 201)
        else:
            return Response("Authentication failed", 401)
    return Response("", 404)


@app.route("/api/remove_project", method=["DELETE"])
@user
@check_configs
def remove_project():
    if request.headers.get("Content-Type") == "application/json":
        project_name = request.json.get("project_name")
        authentication = request.json.get("authentication")
        if authentication == configs.vcs_token:
            scheduler.cancel(project_name)
        else:
            return Response("Authentication failed", 401)
        return Response("Removed", 200)


@app.route("/api/")
@check_configs
def home():
    """Return repos and projects which are running on the server.
    """
    result = {"repos": [], "projects": []}
    result["repos"] = RepoRun.distinct("repo")
    result["projects"] = ProjectRun.distinct("name")
    result_json = json.dumps(result)
    return result_json


@app.route("/api/repos/<repo:path>")
@check_configs
def branch(repo):
    """Returns tests ran on this repo with specific branch or test details if id is sent.

    :param repo: repo's name
    :param branch: the branch's name in the repo
    :param id: DB id of test details.
    """
    branch = request.query.get("branch")
    id = request.query.get("id")

    if id:
        repo_run = RepoRun(id=id)
        result = json.dumps(repo_run.result)
        return result
    if branch:
        fields = ["status", "commit", "committer", "timestamp"]
        where = f'repo="{repo}" and branch="{branch}"'
        repo_runs = RepoRun.get_objects(fields=fields, where=where, order_by="timestamp", asc=False)
        result = json.dumps(repo_runs)
        return result

    VCSObject = VCSFactory().get_cvn(repo=repo)
    exist_branches = VCSObject.get_branches()
    all_branches = RepoRun.distinct(field="branch", where=f"repo='{repo}'")
    deleted_branches = list(set(all_branches) - set(exist_branches))
    branches = {"exist": exist_branches, "deleted": deleted_branches}
    result = json.dumps(branches)
    return result


@app.route("/api/run_config/<name:path>", method=["GET", "POST", "DELETE"])
@user
@check_configs
def run_config(name):
    run_config = RunConfig.find(name=name)
    if run_config and len(run_config) == 1:
        run_config = run_config[0]
    else:
        run_config = RunConfig(name=name)
    if request.method == "POST":
        key = request.json["key"]
        value = request.json["value"]
        run_config.env[key] = value
        run_config.save()
        return Response("Added", 201)
    elif request.method == "DELETE":
        key = request.json["key"]
        run_config.env.pop(key)
        run_config.save()
        return Response("Deleted", 201)
    else:
        env = json.dumps(run_config.env)
        return env
    return abort(404)


@app.route("/api/projects/<project>")
@check_configs
def project(project):
    """Returns tests ran on this project or test details if id is sent.

    :param project: project's name
    :param id: DB id of test details.
    """
    id = request.query.get("id")
    if id:
        project_run = ProjectRun(id=id)
        result = json.dumps(project_run.result)
        return result

    fields = ["status", "timestamp"]
    where = f"name='{project}'"
    project_runs = RepoRun.get_objects(fields=fields, where=where, order_by="timestamp", asc=False)
    result = json.dumps(project_runs)
    return result


@app.route("/status")
@check_configs
def status():
    """Returns repo's branch or project status for your version control system.
    """
    project = request.query.get("project")
    repo = request.query.get("repo")
    branch = request.query.get("branch")
    result = request.query.get("result")  # to return the run result
    fields = ["status"]
    if project:
        where = f"name='{project}' and status!='pending'"
        project_run = ProjectRun.get_objects(fields=fields, where=where, order_by="timestamp", asc=False)
        if len(project_run) == 0:
            return abort(404)

        if result:
            link = f"{configs.domain}/projects/{project}?id={str(project_run[0]['id'])}"
            return redirect(link)
        if project_run[0]["status"] == "success":
            return static_file("svgs/build_passing.svg", mimetype="image/svg+xml", root=".")
        else:
            return static_file("svgs/build_failing.svg", mimetype="image/svg+xml", root=".")

    elif repo:
        if not branch:
            branch = "master"
        where = f"repo='{repo}' and branch='{branch}' and status!='pending'"
        repo_run = RepoRun.get_objects(fields=fields, where=where, order_by="timestamp", asc=False)
        if len(repo_run) == 0:
            return abort(404)
        if result:
            link = f"{configs.domain}/repos/{repo.replace('/', '%2F')}/{branch}/{str(repo_run[0]['id'])}"
            return redirect(link)
        if repo_run[0]["status"] == "success":
            return static_file("svgs/build_passing.svg", mimetype="image/svg+xml", root=".")
        else:
            return static_file("svgs/build_failing.svg", mimetype="image/svg+xml", root=".")

    return abort(404)


@app.route("/static/<filepath:path>")
def static(filepath):
    return static_file(filepath, root="../dist/static")


@app.route("/")
@app.route("/<path:path>")
@check_configs
def catch_all(path=""):
    return static_file("index.html", root="../dist")


session_opts = {"session.type": "file", "session.data_dir": "./data", "session.auto": True}
app_with_session = SessionMiddleware(app, session_opts)
if __name__ == "__main__":
    server = WSGIServer(("0.0.0.0", 6010), app_with_session, handler_class=WebSocketHandler)
    server.serve_forever()

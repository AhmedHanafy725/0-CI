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
from models.scheduler_run import SchedulerRun
from models.trigger_run import TriggerRun
from models.run_config import RunConfig
from models.initial_config import InitialConfig
from models.schedule_info import ScheduleInfo
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
        trigger_run = TriggerRun(id=id)
        trigger_run.status = status
        trigger_run.result = []
        trigger_run.save()
        r.ltrim(id, -1, 0)
        r.publish(f"{trigger_run.repo}_{trigger_run.branch}", json.dumps({"id": id, "status": status}))
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
            trigger_run = TriggerRun(**data)
            trigger_run.save()
            id = str(trigger_run.id)
            data["id"] = id
            r.publish(f"{repo}_{branch}", json.dumps(data))
    if id:
        link = (
            f"{configs.domain}/repos/{trigger_run.repo.replace('/', '%2F')}/{trigger_run.branch}/{str(trigger_run.id)}"
        )
        VCSObject = VCSFactory().get_cvn(repo=trigger_run.repo)
        VCSObject.status_send(status=status, link=link, commit=trigger_run.commit)
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


@app.route("/websocket/schedules/<schedule>")
def update_schedules_table(schedule):
    wsock = request.environ.get("wsgi.websocket")
    if not wsock:
        abort(400, "Expected WebSocket request.")

    sub = r.pubsub()
    sub.subscribe(schedule)
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
            elif conf is "repos" and not isinstance(value, list):
                return Response("repos should be str or list", 400)
            elif conf is not "repos" and not isinstance(value, str):
                return Response(f"{conf} should be str", 400)
            else:
                setattr(configs, conf, value)

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
            run = TriggerRun.get_objects(fields=["status"], where=where)
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
        run = TriggerRun.get_objects(fields=["status"], where=where)
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


@app.route("/api/schedule", method=["GET", "POST", "DELETE"])
@user
@check_configs
def schedule():
    if request.method == "GET":
        schedule_name = request.query.get("schedule_name")
        if schedule_name:
            schedule_info = ScheduleInfo(name=schedule_name)
            info = {
                "schedule_name": schedule_name,
                "install_script": schedule_info.install_script,
                "test_script": schedule_info.test_script,
                "prequisties": schedule_info.prequisties,
                "run_time": schedule_info.run_time,
            }
            return json.dumps(info)

        schedules_names = ScheduleInfo.distinct("name")
        return json.dumps(schedules_names)

    if request.headers.get("Content-Type") == "application/json":
        if request.method == "POST":
            data = ["schedule_name", "run_time"]
            list_str_data = ["install_script", "test_script", "prequisties"]
            data.extend(list_str_data)
            job = {}
            for item in data:
                value = request.json.get(item)
                if not value:
                    return Response(f"{item} should have a value", 400)
                elif item in list_str_data and not isinstance(value, (str, list)):
                    return Response(f"{item} should be str or list", 400)
                elif item not in list_str_data and not isinstance(value, str):
                    return Response(f"{item} should be str", 400)
                else:
                    job[item] = value

            if isinstance(job["install_script"], list):
                job["install_script"] = " && ".join(job["install_script"])

            if isinstance(job["test_script"], str):
                job["test_script"] = [job["test_script"]]

            if job["schedule_name"] in ScheduleInfo.distinct("name"):
                return Response("Schedule name {job['schedule_name']} is already used", 400)

            schedule_info = ScheduleInfo(**job)
            schedule_info.save()
            try:
                scheduler.cron(
                    cron_string=job["run_time"],
                    func=actions.schedule_run,
                    args=[job["schedule_name"], job["install_script"], job["test_script"], job["prequisties"],],
                    id=job["schedule_name"],
                    timeout=7200,
                )
            except:
                return Response("Wrong time format should be like (0 * * * *)", 400)
            return Response("Added", 201)
        else:
            schedule_name = request.json.get("schedule_name")
            schedule_info = ScheduleInfo(name=schedule_name)
            schedule_info.delete()
            scheduler.cancel(schedule_name)
            return Response("Removed", 200)
    return abort(400)


@app.route("/api/schedule_trigger", method=["POST", "GET"])
@user
@check_configs
def schedule_trigger():
    if request.method == "GET":
        redirect("/")

    if request.headers.get("Content-Type") == "application/json":
        schedule_name = request.json.get("schedule_name")

        where = f'schedule_name="{schedule_name}"'
        runs = SchedulerRun.get_objects(fields=["status"], where=where, order_by="timestamp", asc=False)
        if runs and runs[0]["status"] == "pending":
            return Response(
                f"There is a running job from this schedule {schedule_name}, please try again after this run finishes",
                503,
            )
        if schedule_name not in ScheduleInfo.distinct("name"):
            return Response(f"Schedule name {schedule_name} is not found", 400)

        schedule_info = ScheduleInfo(name=schedule_name)
        job = q.enqueue_call(
            func=actions.schedule_run,
            args=(schedule_name, schedule_info.install_script, schedule_info.test_script, schedule_info.prequisties,),
            result_ttl=5000,
            timeout=20000,
        )
        if job:
            return Response(job.get_id(), 200)
    return Response("Wrong data", 400)


@app.route("/api/")
@check_configs
def home():
    """Return repos and schedules which are running on the server.
    """
    result = {"repos": [], "schedules": []}
    result["repos"] = TriggerRun.distinct("repo")
    result["schedules"] = SchedulerRun.distinct("schedule_name")
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
        trigger_run = TriggerRun(id=id)
        result = json.dumps(trigger_run.result)
        return result
    if branch:
        fields = ["status", "commit", "committer", "timestamp"]
        where = f'repo="{repo}" and branch="{branch}"'
        trigger_runs = TriggerRun.get_objects(fields=fields, where=where, order_by="timestamp", asc=False)
        result = json.dumps(trigger_runs)
        return result

    VCSObject = VCSFactory().get_cvn(repo=repo)
    exist_branches = VCSObject.get_branches()
    all_branches = TriggerRun.distinct(field="branch", where=f"repo='{repo}'")
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


@app.route("/api/schedules/<schedule>")
@check_configs
def schedules(schedule):
    """Returns tests ran on this schedule or test details if id is sent.

    :param schedule: schedule's name
    :param id: DB id of test details.
    """
    id = request.query.get("id")
    if id:
        scheduler_run = SchedulerRun(id=id)
        result = json.dumps(scheduler_run.result)
        return result

    fields = ["status", "timestamp"]
    where = f"schedule_name='{schedule}'"
    scheduler_runs = SchedulerRun.get_objects(fields=fields, where=where, order_by="timestamp", asc=False)
    result = json.dumps(scheduler_runs)
    return result


@app.route("/status")
@check_configs
def status():
    """Returns repo's branch or schedule status for your version control system.
    """
    schedule = request.query.get("schedule")
    repo = request.query.get("repo")
    branch = request.query.get("branch")
    result = request.query.get("result")  # to return the run result
    fields = ["status"]
    if schedule:
        where = f"schedule_name='{schedule}' and status!='pending'"
        scheduler_run = SchedulerRun.get_objects(fields=fields, where=where, order_by="timestamp", asc=False)
        if len(scheduler_run) == 0:
            return abort(404)

        if result:
            link = f"{configs.domain}/schedules/{schedule}?id={str(scheduler_run[0]['id'])}"
            return redirect(link)
        if scheduler_run[0]["status"] == "success":
            return static_file("svgs/build_passing.svg", mimetype="image/svg+xml", root=".")
        else:
            return static_file("svgs/build_failing.svg", mimetype="image/svg+xml", root=".")

    elif repo:
        if not branch:
            branch = "master"
        where = f"repo='{repo}' and branch='{branch}' and status!='pending'"
        trigger_run = TriggerRun.get_objects(fields=fields, where=where, order_by="timestamp", asc=False)
        if len(trigger_run) == 0:
            return abort(404)
        if result:
            link = f"{configs.domain}/repos/{repo.replace('/', '%2F')}/{branch}/{str(trigger_run[0]['id'])}"
            return redirect(link)
        if trigger_run[0]["status"] == "success":
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

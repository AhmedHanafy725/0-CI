from datetime import datetime
import os
import json

from flask import Flask, request, send_file, render_template, abort, Response, redirect
from rq import Queue
from rq.job import Job
from flask_cors import CORS
from rq_scheduler import Scheduler
from redis import Redis

from utils.config import Configs
from packages.vcs.vcs import VCSFactory
from worker import conn
from actions.actions import Actions
from bcdb.bcdb import RepoRun, ProjectRun

configs = Configs()
actions = Actions()

app = Flask(__name__, static_folder="../dist/static", template_folder="../dist")

CORS(app, resources={r"/*": {"origins": "*"}})

q = Queue(connection=conn)
scheduler = Scheduler(connection=Redis())


@app.after_request
def set_response_headers(response):
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def trigger(repo, branch, commit, committer):
    if repo in configs.repos:
        status = "pending"
        repo_run = RepoRun(
            timestamp=datetime.now().timestamp(),
            status=status,
            repo=repo,
            branch=branch,
            commit=commit,
            committer=committer,
        )
        repo_run.save()
        id = str(repo_run.id)
        VCSObject = VCSFactory().get_cvn(repo=repo)
        VCSObject.status_send(status=status, link=configs.domain, commit=commit)
        job = q.enqueue_call(func=actions.build_and_test, args=(id,), result_ttl=5000, timeout=20000)
        return job
    return None


@app.route("/git_trigger", methods=["POST"])
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


@app.route("/run_trigger", methods=["POST"])
def run_trigger():
    # this api should be protected by user
    if request.headers.get("Content-Type") == "application/json":
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


@app.route("/api/add_project", methods=["POST"])
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


@app.route("/api/remove_project", methods=["DELETE"])
def remove_project():
    if request.headers.get("Content-Type") == "application/json":
        project_name = request.json.get("project_name")
        authentication = request.json.get("authentication")
        if authentication == configs.vcs_token:
            scheduler.cancel(project_name)
        else:
            return Response("Authentication failed", 401)
        return "Removed", 200


@app.route("/api/")
def home():
    """Return repos and projects which are running on the server.
    """
    result = {"repos": [], "projects": []}
    result["repos"] = RepoRun.distinct("repo")
    result["projects"] = ProjectRun.distinct("name")
    result_json = json.dumps(result)
    return result_json, 200


@app.route("/api/repos/<path:repo>")
def branch(repo):
    """Returns tests ran on this repo with specific branch or test details if id is sent.

    :param repo: repo's name
    :param branch: the branch's name in the repo
    :param id: DB id of test details.
    """
    branch = request.args.get("branch")
    id = request.args.get("id")

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


@app.route("/api/projects/<project>")
def project(project):
    """Returns tests ran on this project or test details if id is sent.

    :param project: project's name
    :param id: DB id of test details.
    """
    id = request.args.get("id")
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
def status():
    """Returns repo's branch or project status for your version control system.
    """
    project = request.args.get("project")
    repo = request.args.get("repo")
    branch = request.args.get("branch")
    result = request.args.get("result")  # to return the run result
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
            return send_file("svgs/build_passing.svg", mimetype="image/svg+xml")
        else:
            return send_file("svgs/build_failing.svg", mimetype="image/svg+xml")

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
            return send_file("svgs/build_passing.svg", mimetype="image/svg+xml")
        else:
            return send_file("svgs/build_failing.svg", mimetype="image/svg+xml")

    return abort(404)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    return render_template("index.html")


if __name__ == "__main__":
    app.run("0.0.0.0", 6010)

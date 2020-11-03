import json
import os
from datetime import datetime

from redis import Redis
from rq import Queue

from actions.actions import Actions
from apis.base import app, check_configs, user
from bottle import HTTPResponse, redirect, request
from models.initial_config import InitialConfig
from models.run import Run
from packages.vcs.vcs import VCSFactory

BIN_DIR = "/zeroci/bin/"

redis = Redis()
actions = Actions()
q = Queue(connection=redis)
PENDING = "pending"


def trigger(repo="", branch="", commit="", committer="", id=None, triggered=True):
    configs = InitialConfig()
    status = PENDING
    timestamp = datetime.now().timestamp()
    if id:
        # Triggered from id.
        run = Run.get(id=id)
        triggered_by = request.environ.get("beaker.session").get("username").strip(".3bot")
        data = {
            "timestamp": timestamp,
            "commit": run.commit,
            "committer": run.committer,
            "status": status,
            "repo": run.repo,
            "branch": run.branch,
            "triggered_by": triggered_by,
            "bin_release": None,
            "id": id,
        }
        run.timestamp = int(timestamp)
        run.status = status
        run.result = []
        run.triggered_by = triggered_by
        if run.bin_release:
            bin_path = os.path.join(BIN_DIR, run.repo, run.branch, run.bin_release)
            if os.path.exists(bin_path):
                os.remove(bin_path)
        run.bin_release = None
        run.save()
        for key in redis.keys():
            if id in key.decode():
                redis.delete(key)
        redis.publish("zeroci_status", json.dumps(data))
    else:
        # Triggered from vcs webhook or rebuild using the button.
        if repo in configs.repos:
            triggered_by = "VCS Hook"
            if triggered:
                triggered_by = request.environ.get("beaker.session").get("username").strip(".3bot")
            data = {
                "timestamp": timestamp,
                "commit": commit,
                "committer": committer,
                "status": status,
                "repo": repo,
                "branch": branch,
                "triggered_by": triggered_by,
                "bin_release": None,
            }
            run = Run(**data)
            run.save()
            id = str(run.id)
            data["id"] = id
            redis.publish("zeroci_status", json.dumps(data))
    if id:
        link = f"{configs.domain}/repos/{run.repo}/{run.branch}/{str(run.id)}"
        vcs_obj = VCSFactory().get_cvn(repo=run.repo)
        vcs_obj.status_send(status=status, link=link, commit=run.commit)
        job = q.enqueue_call(func=actions.build_and_test, args=(id,), result_ttl=5000, timeout=20000)
        return job
    return None


@app.route("/git_trigger", method=["POST"])
@check_configs
def git_trigger():
    """Trigger the test when a post request is sent from a repo's webhook.
    """
    configs = InitialConfig()
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
                job = trigger(repo=repo, branch=branch, commit=commit, committer=committer, triggered=False)
                if job:
                    return HTTPResponse(job.get_id(), 200)
        return HTTPResponse("Done", 200)
    return HTTPResponse("Wrong content type", 400)


@app.route("/api/run_trigger", method=["POST", "GET"])
@user
@check_configs
def run_trigger():
    if request.method == "GET":
        redirect("/")

    if request.headers.get("Content-Type") == "application/json":
        id = request.json.get("id")
        if id:
            run = Run.get(id=id)
            if run.status == PENDING:
                return HTTPResponse(
                    f"There is a running job for this id {id}, please try again after this run finishes", 503
                )
            job = trigger(id=id)
            return HTTPResponse(job.get_id(), 200)

        repo = request.json.get("repo")
        branch = request.json.get("branch")
        vcs_obj = VCSFactory().get_cvn(repo=repo)
        last_commit = vcs_obj.get_last_commit(branch=branch)
        committer = vcs_obj.get_committer(commit=last_commit)
        where = {"repo": repo, "branch": branch, "commit": last_commit, "status": PENDING}
        run = Run.get_objects(fields=["status"], **where)
        if run:
            return HTTPResponse(
                f"There is a running job from this commit {last_commit}, please try again after this run finishes", 503
            )
        if last_commit:
            job = trigger(repo=repo, branch=branch, commit=last_commit, committer=committer)
        else:
            return HTTPResponse(f"Couldn't get last commit from this branch {branch}, please try again", 503)
        if job:
            return HTTPResponse(job.get_id(), 200)
        return HTTPResponse("Wrong data", 400)

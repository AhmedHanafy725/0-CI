import json

from actions.trigger import Trigger
from bottle import HTTPResponse, redirect, request
from models.initial_config import InitialConfig
from models.run import Run
from packages.vcs.vcs import VCSFactory
from redis import Redis
from rq import Queue
from utils.constants import PENDING

from apis.base import app, check_configs, user

trigger = Trigger()
q = Queue(connection=Redis(), name="zeroci")


@app.route("/git_trigger", method=["POST"])
@check_configs
def git_trigger():
    """Trigger the test when a post request is sent from a repo's webhook."""
    # TODO: make payload validation before work on it.
    configs = InitialConfig()
    if request.headers.get("Content-Type") == "application/json":
        job = ""
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
                job = q.enqueue_call(
                    trigger.enqueue,
                    args=(repo, branch, commit, committer, "", None, False),
                    result_ttl=5000,
                    timeout=20000,
                )

        # pull case
        # TODO: Handle the request for gitea.
        elif request.json.get("pull_request"):
            if request.json.get("action") in ["opened", "synchronize"]:
                repo = request.json["pull_request"]["head"]["repo"]["full_name"]
                branch = request.json["pull_request"]["head"]["ref"]
                target_branch = request.json["pull_request"]["base"]["ref"]
                commit = request.json["pull_request"]["head"]["sha"]
                committer = request.json["sender"]["login"]
                job = q.enqueue_call(
                    trigger.enqueue,
                    args=(repo, branch, commit, committer, target_branch, None, False),
                    result_ttl=5000,
                    timeout=20000,
                )
        if job:
            return HTTPResponse(job.get_id(), 201)
        return HTTPResponse("Nothing to be done", 200)
    return HTTPResponse("Wrong content type", 400)


@app.route("/api/run_trigger", method=["POST", "GET"])
@user
@check_configs
def run_trigger():
    if request.method == "GET":
        redirect("/")

    if request.headers.get("Content-Type") == "application/json":
        run_id = request.json.get("id")
        if run_id:
            run = Run.get(run_id=run_id)
            if run.status == PENDING:
                return HTTPResponse(
                    f"There is a running job for this run_id {run_id}, please try again after this run finishes", 503
                )
            job = q.enqueue_call(
                trigger.enqueue, args=("", "", "", "", "", run_id, True), result_ttl=5000, timeout=20000
            )
            if job:
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
            job = q.enqueue_call(
                trigger.enqueue,
                args=(repo, branch, last_commit, committer, "", None, True),
                result_ttl=5000,
                timeout=20000,
            )
        else:
            return HTTPResponse(f"Couldn't get last commit from this branch {branch}, please try again", 503)
        if job:
            return HTTPResponse(job.get_id(), 200)
        return HTTPResponse("Wrong data", 400)

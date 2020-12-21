import json

from apis.base import app, check_configs, user
from bottle import HTTPResponse, redirect, request
from models.initial_config import InitialConfig
from models.run import Run
from packages.vcs.vcs import VCSFactory
from actions.trigger import Trigger

trigger = Trigger()

PENDING = "pending"


@app.route("/git_trigger", method=["POST"])
@check_configs
def git_trigger():
    """Trigger the test when a post request is sent from a repo's webhook.
    """
    # TODO: handle the case of running from push and pull request to not run it twice.
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
                job = trigger.enqueue(repo=repo, branch=branch, commit=commit, committer=committer)

        # pull case
        # TODO: Handle the request for gitea.
        elif request.json.get("pull_request"):
            if request.json.get("action") in ["opened", "synchronize"]:
                repo = request.json["pull_request"]["head"]["repo"]["full_name"]
                current_branch = request.json["pull_request"]["head"]["ref"]
                target_branch = request.json["pull_request"]["base"]["ref"]
                commit = request.json["pull_request"]["head"]["sha"]
                committer = request.json["sender"]["login"]
                job = trigger.enqueue(repo=repo, branch=current_branch, commit=commit, committer=committer, target_branch=target_branch)
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
            job = trigger.enqueue(run_id=run_id, triggered=True)
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
            job = trigger.enqueue(repo=repo, branch=branch, commit=last_commit, committer=committer, triggered=True)
        else:
            return HTTPResponse(f"Couldn't get last commit from this branch {branch}, please try again", 503)
        if job:
            return HTTPResponse(job.get_id(), 200)
        return HTTPResponse("Wrong data", 400)

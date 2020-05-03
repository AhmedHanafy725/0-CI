import json
from datetime import datetime

from redis import Redis
from rq import Queue

from actions.actions import Actions
from apis.base import app, check_configs, configs, user
from bottle import Response, redirect, request
from models.trigger_run import TriggerRun
from packages.vcs.vcs import VCSFactory

redis = Redis()
actions = Actions()
q = Queue(connection=redis)


def trigger(repo="", branch="", commit="", committer="", id=None):
    status = "pending"
    timestamp = datetime.now().timestamp()
    if id:
        trigger_run = TriggerRun(id=id)
        trigger_run.status = status
        trigger_run.result = []
        trigger_run.save()
        redis.ltrim(id, -1, 0)
        redis.publish(f"{trigger_run.repo}_{trigger_run.branch}", json.dumps({"id": id, "status": status}))
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
            redis.publish(f"{repo}_{branch}", json.dumps(data))
    if id:
        link = (
            f"{configs.domain}/repos/{trigger_run.repo.replace('/', '%2F')}/{trigger_run.branch}/{str(trigger_run.id)}"
        )
        vcs_obj = VCSFactory().get_cvn(repo=trigger_run.repo)
        vcs_obj.status_send(status=status, link=link, commit=trigger_run.commit)
        job = q.enqueue_call(func=actions.build_and_test, args=(id,), result_ttl=5000, timeout=20000)
        return job
    return None


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

import json

from apis.base import app, check_configs
from bottle import abort, redirect, request, static_file
from models.initial_config import InitialConfig
from models.run import Run
from packages.vcs.vcs import VCSFactory


SUCCESS = "success"
FAILURE = "failure"
ERROR = "error"
PENDING = "pending"


@app.route("/api/")
@check_configs
def home():
    """Return repos and schedules which are running on the server.
    """
    configs = InitialConfig()
    result = {"repos": configs.repos}
    return json.dumps(result)


@app.route("/api/repos/<repo:path>")
@check_configs
def result(repo):
    """Returns tests ran on this repo with specific branch or test details if id is sent.

    :param repo: repo's name
    :param branch: the branch's name in the repo
    :param id: DB id of test details.
    """
    branch = request.query.get("branch")
    id = request.query.get("id")

    if id:
        run = Run.get(id=id)
        live = True if run.status == PENDING else False
        return json.dumps({"live": live, "result": run.result})

    if branch:
        fields = ["status", "commit", "committer", "timestamp", "bin_release", "triggered_by"]
        where = {"repo": repo, "branch": branch}
        runs = Run.get_objects(fields=fields, order_by="timestamp", asc=False, **where)
        return json.dumps(runs)

    vcs_obj = VCSFactory().get_cvn(repo=repo)
    exist_branches = vcs_obj.get_branches()
    all_branches = Run.distinct(field="branch", repo=repo)
    deleted_branches = list(set(all_branches) - set(exist_branches))
    branches = {"exist": exist_branches, "deleted": deleted_branches}
    return json.dumps(branches)


@app.route("/status")
@check_configs
def status():
    """Returns repo's branch or schedule status for your version control system.
    """
    repo = request.query.get("repo")
    branch = request.query.get("branch")
    result = request.query.get("result")  # to return the run result
    fields = ["status"]
    configs = InitialConfig()

    if not repo:
        return abort(400, "repo is missing")
    if not branch:
        return abort(400, "branch is missing")
    where = {"repo": repo, "branch": branch, "status": f"{ERROR} OR {FAILURE} OR {SUCCESS}"}
    run = Run.get_objects(fields=fields, order_by="timestamp", asc=False, **where)
    if len(run) == 0:
        return abort(404)
    if result:
        link = f"{configs.domain}/repos/{repo.replace('/', '%2F')}/{branch}/{str(run[0]['id'])}"
        return redirect(link)
    if run[0]["status"] == SUCCESS:
        return static_file("svgs/build_passing.svg", mimetype="image/svg+xml", root=".")
    else:
        return static_file("svgs/build_failing.svg", mimetype="image/svg+xml", root=".")

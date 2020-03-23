import json

from redis import Redis

from bcdb.bcdb import InitialConfig
from packages.telegram.telegram import Telegram
from packages.vcs.vcs import VCSFactory

telegram = Telegram()
r = Redis()
SUCCESS = "success"
FAILURE = "failure"


class Reporter(InitialConfig):
    def report(self, id, db_run, project_name=None):
        """Report the result to the commit status and Telegram chat.

        :param status: test status. 
        :type status: str
        :param file_name: result file name. 
        :type file_name: str
        :param repo: full repo name
        :type repo: str
        :param branch: branch name. 
        :type branch: str
        :param commit: commit hash.
        :type commit: str
        :param committer: committer name. 
        :type committer: str
        """
        run = db_run(id=id)
        msg = self.report_msg(status=run.status, project_name=project_name)
        if not project_name:
            link = f"{self.domain}/repos/{run.repo.replace('/', '%2F')}/{run.branch}/{str(run.id)}"
            r.publish(f"{run.repo}_{run.branch}", json.dumps({"id": id, "status": run.status}))
            VCSObject = VCSFactory().get_cvn(repo=run.repo)
            VCSObject.status_send(status=run.status, link=link, commit=run.commit)
            telegram.send_msg(
                msg=msg, link=link, repo=run.repo, branch=run.branch, commit=run.commit, committer=run.committer
            )
        else:
            link = f"{self.domain}/projects/{run.name.replace(' ', '%20')}/{str(run.id)}"
            r.publish(project_name, json.dumps({"id": id, "status": run.status}))
            telegram.send_msg(msg=msg, link=link)

    def report_msg(self, status, project_name=None):
        if project_name:
            name = f"{project_name} tests"
        else:
            name = "Tests"
        if status == SUCCESS:
            msg = f"✅ {name} passed "
        elif status == FAILURE:
            msg = f"❌ {name} failed "
        else:
            msg = f"⛔️ {name} errored "

        return msg

import json
from urllib.parse import urljoin

from redis import Redis

from models.initial_config import InitialConfig
from packages.telegram.telegram import Telegram
from packages.vcs.vcs import VCSFactory

r = Redis()
SUCCESS = "success"
FAILURE = "failure"


class Reporter:
    def report(self, run_id, run_obj):
        """Report the result to the commit status and Telegram chat.

        :param run_id: DB's run_id of this run details.
        :type run_id: str
        :param parent_model: the class that the passed id is belonging to.
        :type parent_model: class
        :param schedule_name: it will have a value if the run is scheduled.
        :param schedule_name: str
        """
        configs = InitialConfig()
        telegram = Telegram()
        bin_release = run_obj.bin_release
        triggered_by = run_obj.triggered_by
        msg = self.report_msg(status=run_obj.status)
        url = f"/repos/{run_obj.repo}/{run_obj.branch}/{run_obj.run_id}"
        link = urljoin(configs.domain, url)
        if bin_release:
            bin_url = f"/bin/{run_obj.repo}/{run_obj.branch}/{bin_release}"
            bin_link = urljoin(configs.domain, bin_url)
        else:
            bin_link = None
        data = {
            "timestamp": run_obj.timestamp,
            "commit": run_obj.commit,
            "committer": run_obj.committer,
            "status": run_obj.status,
            "repo": run_obj.repo,
            "branch": run_obj.branch,
            "bin_release": bin_release,
            "triggered_by": triggered_by,
            "run_id": run_id,
        }
        r.publish("zeroci_status", json.dumps(data))
        vcs_obj = VCSFactory().get_cvn(repo=run_obj.repo)
        vcs_obj.status_send(status=run_obj.status, link=link, commit=run_obj.commit)
        telegram.send_msg(
            msg=msg,
            link=link,
            repo=run_obj.repo,
            branch=run_obj.branch,
            commit=run_obj.commit,
            committer=run_obj.committer,
            bin_link=bin_link,
            triggered_by=triggered_by,
        )

    def report_msg(self, status):
        if status == SUCCESS:
            msg = f"✅ Run passed "
        elif status == FAILURE:
            msg = f"❌ Run failed "
        else:
            msg = f"⛔️ Run errored "

        return msg

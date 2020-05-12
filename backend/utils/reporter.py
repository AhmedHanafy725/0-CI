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
    def report(self, id, parent_model, schedule_name=None):
        """Report the result to the commit status and Telegram chat.

        :param id: DB's id of this run details.
        :type id: str
        :param parent_model: the class that the passed id is belonging to.
        :type parent_model: class
        :param schedule_name: it will have a value if the run is scheduled.
        :param schedule_name: str
        """
        configs = InitialConfig()
        telegram = Telegram()
        model_obj = parent_model(id=id)
        msg = self.report_msg(status=model_obj.status, schedule_name=schedule_name)
        if not schedule_name:
            unslash_repo = model_obj.repo.replace("/", "%2F")
            url = f"/repos/{unslash_repo}/{model_obj.branch}/{model_obj.id}"
            link = urljoin(configs.domain, url)
            r.publish(f"{model_obj.repo}_{model_obj.branch}", json.dumps({"id": id, "status": model_obj.status}))
            vcs_obj = VCSFactory().get_cvn(repo=model_obj.repo)
            vcs_obj.status_send(status=model_obj.status, link=link, commit=model_obj.commit)
            telegram.send_msg(
                msg=msg,
                link=link,
                repo=model_obj.repo,
                branch=model_obj.branch,
                commit=model_obj.commit,
                committer=model_obj.committer,
            )
        else:
            unspaced_schedule = model_obj.schedule_name.replace(" ", "%20").replace("/", "%2F")
            url = f"/schedules/{unspaced_schedule}/{model_obj.id}"
            link = urljoin(configs.domain, url)
            r.publish(schedule_name, json.dumps({"id": id, "status": model_obj.status}))
            telegram.send_msg(msg=msg, link=link)

    def report_msg(self, status, schedule_name=None):
        if schedule_name:
            name = f"{schedule_name} tests"
        else:
            name = "Tests"
        if status == SUCCESS:
            msg = f"✅ {name} passed "
        elif status == FAILURE:
            msg = f"❌ {name} failed "
        else:
            msg = f"⛔️ {name} errored "

        return msg

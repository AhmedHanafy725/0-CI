import json
import os
import traceback
from datetime import datetime

import yaml
from bottle import request
from models.initial_config import InitialConfig
from models.run import Run
from models.schedule_info import ScheduleInfo
from packages.vcs.vcs import VCSFactory
from redis import Redis
from rq import Queue

from actions.reporter import Reporter
from actions.runner import Runner
from actions.validator import Validator
from rq_scheduler import Scheduler

reporter = Reporter()
runner = Runner()
scheduler = Scheduler(connection=Redis())

redis = Redis()
q = Queue(connection=redis, name="default")
PENDING = "pending"
ERROR = "error"


ERROR = "error"
LOG_TYPE = "log"
BIN_DIR = "/zeroci/bin/"


class Trigger:
    def _load_config(self, repo, commit):
        vcs_obj = VCSFactory().get_cvn(repo=repo)
        script = vcs_obj.get_content(ref=commit, file_path="zeroCI.yaml")
        if script:
            try:
                config = yaml.safe_load(script)
                return True, config, ""
            except:
                msg = traceback.format_exc()
        else:
            msg = "zeroCI.yaml is not found on the repository's home"
        
        return False, "", msg

    def enqueue(self, repo="", branch="", commit="", committer="", target_branch="", run_id=None, triggered=False):
        if run_id:
            run = Run.get(run_id=run_id)
            repo = run.repo
            commit = run.commit
        status, config, msg = self._load_config(repo, commit)
        if not status:
            run , run_id = self._prepare_run_object(repo=repo, branch=branch, commit=commit, committer=committer, run_id=run_id, triggered=triggered)
            return self._report(msg, run, run_id)
        validator = Validator()
        valid, msg = validator.validate_yaml(config)
        if not valid:
            run , run_id = self._prepare_run_object(repo=repo, branch=branch, commit=commit, committer=committer, run_id=run_id, triggered=triggered)
            return self._report(msg, run, run_id)
        
        if run_id:
            run , run_id = self._prepare_run_object(run_id=run_id, triggered=triggered)
            return self._trigger(repo_config=config, run=run, run_id=run_id)

        push = config["run_on"].get("push")
        pull_request = config["run_on"].get("pull_request")
        manual = config["run_on"].get("manual")
        schedule = config["run_on"].get("schedule")

        if repo and branch and not schedule:
            schedule_name = f"{repo}_{branch}"
            scheduler.cancel(schedule_name)
        if push:
            trigger_branches = push["branches"]
            if branch and branch in trigger_branches:
                run , run_id = self._prepare_run_object(repo=repo, branch=branch, commit=commit, committer=committer, triggered=triggered)
                return self._trigger(repo_config=config, run=run, run_id=run_id)
        if pull_request:
            target_branches = pull_request["branches"]
            if target_branch and target_branch in target_branches:
                run , run_id = self._prepare_run_object(repo=repo, branch=branch, commit=commit, committer=committer, triggered=triggered)
                return self._trigger(repo_config=config, run=run, run_id=run_id)
        if manual and triggered:
            trigger_branches = manual["branches"]
            if branch and branch in trigger_branches:
                run , run_id = self._prepare_run_object(repo=repo, branch=branch, commit=commit, committer=committer, triggered=triggered)
                return self._trigger(repo_config=config, run=run, run_id=run_id)
        if schedule:
            schedule_branch = schedule["branch"]
            cron = schedule["cron"]
            schedule_name = f"{repo}_{branch}"
            if branch == schedule_branch:
                scheduler.cron(
                    cron_string=cron,
                    func=self._trigger_schedule,
                    args=[repo, branch],
                    id=schedule_name,
                    timeout=-1,
                )
        return

    def _prepare_run_object(self, repo="", branch="", commit="", committer="", run_id=None, triggered=False):
        configs = InitialConfig()
        status = PENDING
        timestamp = datetime.now().timestamp()
        if run_id:
            # Triggered from id.
            run = Run.get(run_id=run_id)
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
                "run_id": run_id,
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
                if run_id in key.decode():
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
                run_id = str(run.run_id)
                data["run_id"] = run_id
                redis.publish("zeroci_status", json.dumps(data))
        if run and run_id:
            return run, run_id
        return None, None

    def _trigger(self, repo_config, run, run_id):
        if run and run_id:
            configs = InitialConfig()
            link = f"{configs.domain}/repos/{run.repo}/{run.branch}/{str(run.run_id)}"
            vcs_obj = VCSFactory().get_cvn(repo=run.repo)
            vcs_obj.status_send(status=PENDING, link=link, commit=run.commit)
            #TODO: before triggering, check that there is not a run with same commit and in state pending.
            job = q.enqueue_call(func=runner.build_and_test, args=(run_id, repo_config), result_ttl=5000, timeout=20000)
            return job
        return

    def _trigger_schedule(self, repo, branch):
        vcs_obj = VCSFactory().get_cvn(repo=repo)
        last_commit = vcs_obj.get_last_commit(branch=branch)
        committer = vcs_obj.get_committer(commit=last_commit)
        where = {"repo": repo, "branch": branch, "commit": last_commit, "status": PENDING}
        exist_run = Run.get_objects(fields=["status"], **where)
        run, run_id = self._prepare_run_object(repo=repo, branch=branch, commit=last_commit, committer=committer)
        if exist_run:
            msg = f"There is a running job from this commit {last_commit}"
            return self._report(msg, run, run_id)
        run.triggered_by = "ZeroCI Scheduler"
        run.save()
        status, config, msg = self._load_config(repo, last_commit)
        if not status:
            return self._report(msg, run, run_id)
        validator = Validator()
        valid, msg = validator.validate_yaml(config)
        if not valid:
            return self._report(msg, run, run_id)
        runner.build_and_test(run_id, config)

    def _report(self, msg, run, run_id):
        msg = f"{msg} (see examples: https://github.com/threefoldtech/zeroCI/tree/development/docs/config)"
        redis.rpush(run_id, msg)
        run.result.append({"type": LOG_TYPE, "status": ERROR, "name": "Yaml File", "content": msg})
        run.status = ERROR
        run.save()
        reporter.report(run_id=run_id, run_obj=run)
        return

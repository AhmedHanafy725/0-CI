import json
import os
import traceback
from datetime import datetime

import yaml
from bottle import request
from models.initial_config import InitialConfig
from models.run import TriggerModel
from packages.vcs.vcs import VCSFactory
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler
from utils.constants import BIN_DIR, ERROR, LOG_TYPE, PENDING

from actions.reporter import Reporter
from actions.runner import Runner
from actions.validator import validate_yaml


class Trigger:
    def __init__(self):
        self._redis = None
        self._runner = None
        self._reporter = None
        self._queue = None
        self._scheduler = None
        self._vcs = None

    @property
    def redis(self):
        if not self._redis:
            self._redis = Redis()
        return self._redis

    @property
    def runner(self):
        if not self._runner:
            self._runner = Runner()
        return self._runner

    @property
    def reporter(self):
        if not self._reporter:
            self._reporter = Reporter()
        return self._reporter

    @property
    def queue(self):
        if not self._queue:
            self._queue = Queue(connection=self.redis, name="default")
        return self._queue

    @property
    def scheduler(self):
        if not self._scheduler:
            self._scheduler = Scheduler(connection=self.redis)
        return self._scheduler

    @property
    def vcs(self):
        if not self._vcs:
            self._vcs = VCSFactory().get_cvn()
        return self._vcs

    def _load_config(self, repo, commit):
        self.vcs._set_repo_obj(repo=repo)
        script = self.vcs.get_content(ref=commit, file_path="zeroCI.yaml")
        if script:
            try:
                config = yaml.safe_load(script)
                return True, config, ""
            except:
                msg = traceback.format_exc()
        else:
            msg = "zeroCI.yaml is not found on the repository's home"

        return False, "", msg

    def _load_validate_config(
        self, repo="", branch="", commit="", committer="", run_id=None, triggered=False, triggered_by=None
    ):
        if run_id:
            run = TriggerModel.objects.get(run_id=run_id)
            repo = run.repo
            commit = run.commit
        status, config, msg = self._load_config(repo, commit)
        if not status:
            run, run_id = self._prepare_run_object(
                repo=repo,
                branch=branch,
                commit=commit,
                committer=committer,
                run_id=run_id,
                triggered=triggered,
                triggered_by=triggered_by,
            )
            self._report(msg, run, run_id)
            return False
        valid, msg = validate_yaml(config)
        if not valid:
            run, run_id = self._prepare_run_object(
                repo=repo,
                branch=branch,
                commit=commit,
                committer=committer,
                run_id=run_id,
                triggered=triggered,
                triggered_by=triggered_by,
            )
            self._report(msg, run, run_id)
            return False
        return config

    def _prepare_run_object(
        self, repo="", branch="", commit="", committer="", run_id=None, triggered=False, triggered_by=None
    ):
        configs = InitialConfig()
        timestamp = int(datetime.now().timestamp())
        if run_id:
            # Triggered from id.
            run = TriggerModel.objects.get(run_id=run_id)
            triggered_by = triggered_by or request.environ.get("beaker.session").get("username").strip(".3bot")
            data = {
                "timestamp": timestamp,
                "commit": run.commit,
                "committer": run.committer,
                "status": PENDING,
                "repo": run.repo,
                "branch": run.branch,
                "triggered_by": triggered_by,
                "bin_release": None,
                "run_id": run_id,
            }
            run.timestamp = timestamp
            run.status = PENDING
            run.result = []
            run.triggered_by = triggered_by
            if run.bin_release:
                bin_path = os.path.join(BIN_DIR, run.repo, run.branch, run.bin_release)
                if os.path.exists(bin_path):
                    os.remove(bin_path)
            run.bin_release = None
            run.save()
            for key in self.redis.keys():
                if run_id in key.decode():
                    self.redis.delete(key)
            self.redis.publish("zeroci_status", json.dumps(data))
        else:
            # Triggered from vcs webhook or rebuild using the button.
            if repo in configs.repos:
                triggered_by = triggered_by or "VCS Hook"
                if triggered:
                    triggered_by = triggered_by or request.environ.get("beaker.session").get("username").strip(".3bot")
                data = {
                    "timestamp": timestamp,
                    "commit": commit,
                    "committer": committer,
                    "status": PENDING,
                    "repo": repo,
                    "branch": branch,
                    "triggered_by": triggered_by,
                    "bin_release": None,
                }
                run = TriggerModel(**data)
                run.save()
                run_id = str(run.run_id)
                data["run_id"] = run_id
                self.redis.publish("zeroci_status", json.dumps(data))
        if run and run_id:
            return run, run_id
        return None, None

    def enqueue(self, repo="", branch="", commit="", committer="", target_branch="", run_id=None, triggered=False):
        config = self._load_validate_config(
            repo=repo, branch=branch, commit=commit, committer=committer, run_id=run_id, triggered=triggered
        )
        if not config:
            return

        if run_id:
            run, run_id = self._prepare_run_object(run_id=run_id, triggered=triggered)
            return self._trigger(repo_config=config, run=run, run_id=run_id)

        push = config["run_on"].get("push")
        pull_request = config["run_on"].get("pull_request")
        manual = config["run_on"].get("manual")
        schedule = config["run_on"].get("schedule")

        if repo and branch and not schedule:
            schedule_name = f"{repo}_{branch}"
            self.scheduler.cancel(schedule_name)
        if push:
            trigger_branches = push["branches"]
            if branch and branch in trigger_branches:
                run, run_id = self._prepare_run_object(
                    repo=repo, branch=branch, commit=commit, committer=committer, triggered=triggered
                )
                return self._trigger(repo_config=config, run=run, run_id=run_id)
        if pull_request:
            target_branches = pull_request["branches"]
            if target_branch and target_branch in target_branches:
                run, run_id = self._prepare_run_object(
                    repo=repo, branch=branch, commit=commit, committer=committer, triggered=triggered
                )
                return self._trigger(repo_config=config, run=run, run_id=run_id)
        if manual and triggered:
            trigger_branches = manual["branches"]
            if branch and branch in trigger_branches:
                run, run_id = self._prepare_run_object(
                    repo=repo, branch=branch, commit=commit, committer=committer, triggered=triggered
                )
                return self._trigger(repo_config=config, run=run, run_id=run_id)
        if schedule:
            schedule_branch = schedule["branch"]
            cron = schedule["cron"]
            schedule_name = f"{repo}_{branch}"
            if branch == schedule_branch:
                self.scheduler.cron(
                    cron_string=cron,
                    func=self._trigger_schedule,
                    args=[repo, branch],
                    id=schedule_name,
                    timeout=-1,
                )

    def _trigger(self, repo_config, run, run_id):
        if run and run_id:
            configs = InitialConfig()
            link = f"{configs.domain}/repos/{run.repo}/{run.branch}/{str(run.run_id)}"
            self.vcs._set_repo_obj(repo=run.repo)
            self.vcs.status_send(status=PENDING, link=link, commit=run.commit)
            # TODO: before triggering, check that there is not a run with same commit and in state pending.
            job = self.queue.enqueue_call(
                func=self.runner.build_and_test, args=(run_id, repo_config), result_ttl=5000, timeout=20000
            )
            return job

    def _trigger_schedule(self, repo, branch):
        triggered_by = "ZeroCI Scheduler"
        self.vcs._set_repo_obj(repo=repo)
        last_commit = self.vcs.get_last_commit(branch=branch)
        committer = self.vcs.get_committer(commit=last_commit)
        where = {"repo": repo, "branch": branch, "commit": last_commit, "status": PENDING}
        run, run_id = self._prepare_run_object(
            repo=repo, branch=branch, commit=last_commit, committer=committer, triggered_by=triggered_by
        )
        exist_run = TriggerModel.objects(**where).only("status")
        if exist_run:
            msg = f"There is a running job from this commit {last_commit}"
            return self._report(msg, run, run_id)
        config = self._load_validate_config(run_id=run_id, triggered_by=triggered_by)
        if config:
            self.runner.build_and_test(run_id, config)

    def _report(self, msg, run, run_id):
        msg = f"{msg} (see examples: https://github.com/threefoldtech/zeroCI/tree/development/docs/config)"
        self.redis.rpush(run_id, msg)
        run.result.append({"type": LOG_TYPE, "status": ERROR, "name": "Yaml File", "content": msg})
        run.status = ERROR
        run.save()
        self.reporter.report(run_id=run_id, run_obj=run)

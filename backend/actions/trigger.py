import json
import os
import traceback
from datetime import datetime

import yaml
from bottle import request
from models.initial_config import InitialConfig
from models.run import Run
from packages.vcs.vcs import VCSFactory
from redis import Redis
from rq import Queue

from actions.runner import Runner

redis = Redis()
q = Queue(connection=redis)
PENDING = "pending"

ERROR = "error"
LOG_TYPE = "log"
BIN_DIR = "/zeroci/bin/"


class Trigger:
    def _load_yaml(self, repo):
        vcs_obj = VCSFactory().get_cvn(repo=repo)
        script = vcs_obj.get_content(ref=self.run_obj.commit, file_path="zeroCI.yaml")
        if script:
            try:
                return yaml.safe_load(script)
            except:
                msg = traceback.format_exc()
        else:
            msg = "zeroCI.yaml is not found on the repository's home"

        redis.rpush(self.run_id, msg)
        self.run_obj.result.append({"type": LOG_TYPE, "status": ERROR, "name": "Yaml File", "content": msg})
        self.run_obj.save()
        return False

    def enqueue(self, repo="", branch="", commit="", committer="", id=None, triggered=True):
        configs = InitialConfig()
        status = PENDING
        timestamp = datetime.now().timestamp()
        yaml_config = self._load_yaml(repo)
        if yaml_config:
            valid = self.validate_yaml(yaml_config)
            if valid:
                pass #FIXME
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
            job = q.enqueue_call(func=Runner.build_and_test, args=(id,), result_ttl=5000, timeout=20000)
            return job
        return None

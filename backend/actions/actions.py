import json
import os
import traceback
from datetime import datetime
from shutil import rmtree, copyfile
from urllib.parse import urljoin

import redis
import requests
import yaml

from deployment.container import Container
from git import Repo
from kubernetes.client import V1EnvVar
from models.initial_config import InitialConfig
from models.run_config import RunConfig
from models.scheduler_run import SchedulerRun
from models.trigger_run import TriggerRun, TriggerModel
from packages.vcs.vcs import VCSFactory
from utils.reporter import Reporter
from utils.utils import Utils
from actions.yaml_validation import Validator

container = Container()
reporter = Reporter()
utils = Utils()
r = redis.Redis()


class Actions(Validator):
    _REPOS_DIR = "/opt/code/vcs_repos"
    run_id = None
    model_obj = None

    def test_run(self, job):
        """Runs tests and store the result in DB.
        """
        status = "success"
        for line in job["script"]:
            status = "success"
            response, file_path = container.run_test(id=self.run_id, run_cmd=line["cmd"])
            result = response.stdout
            type = "log"
            if response.returncode:
                status = "failure"
            if file_path:
                try:
                    result = utils.xml_parse(path=file_path, line=line["cmd"])
                    type = "testsuite"
                except:
                    pass
                os.remove(file_path)

            name = "{job_name}: {test_name}".format(job_name=job["name"], test_name=line["name"])
            self.model_obj.result.append({"type": type, "status": status, "name": name, "content": result})
            self.model_obj.save()
            if response.returncode in [137, 124]:
                return False
        return True

    def build(self, job, repo_paths, job_number):
        """Create VM with the required prerequisties and run installation steps to get it ready for running tests.
        """
        env = self._get_run_env()
        deployed = container.deploy(env=env, prerequisites=job["prerequisites"], repo_paths=repo_paths)
        installed = False
        if deployed:
            if job_number != 0:
                self._set_bin()
            response = container.execute_command(cmd=job["install"], id=self.run_id)
            if response.returncode:
                name = "{job_name}: Installation".format(job_name=job["name"])
                result = response.stdout
            else:
                installed = True
        else:
            name = "{job_name}: Deploy".format(job_name=job["name"])
            result = "Couldn't deploy a container"
            r.rpush(self.run_id, result)

        if not deployed or not installed:
            self.model_obj.result.append({"type": "log", "status": "error", "name": name, "content": result})
            self.model_obj.save()

        return deployed, installed

    def cal_status(self):
        """Calculate the status of the whole tests result has been stored on the BD's id.
        """
        status = "success"
        for result in self.model_obj.result:
            if result["status"] != "success":
                status = result["status"]
        self.model_obj.status = status
        self.model_obj.save()

    def _get_run_env(self):
        """Get run environment variables.
        """
        if isinstance(self.model_obj, TriggerModel):
            name = self.model_obj.repo
        else:
            name = self.model_obj.schedule_name
        run_config = RunConfig(name=name)
        run_env = run_config.env
        env = []
        for key in run_env.keys():
            env_var = V1EnvVar(name=key, value=run_env.get(key))
            env.append(env_var)
        return env

    def _load_yaml(self):
        vcs_obj = VCSFactory().get_cvn(repo=self.model_obj.repo)
        script = vcs_obj.get_content(ref=self.model_obj.commit, file_path="zeroCI.yaml")
        if script:
            try:
                return yaml.safe_load(script)
            except:
                msg = traceback.format_exc()
        else:
            msg = "zeroCI.yaml is not found on the repository's home"

        r.rpush(self.run_id, msg)
        self.model_obj.result.append({"type": "log", "status": "error", "name": "Yaml File", "content": msg})
        self.model_obj.save()
        return False

    def clone_repo(self):
        """Clone repo.
        """
        configs = InitialConfig()
        repo_remote_path = os.path.join(self._REPOS_DIR, self.model_obj.repo)
        repo_local_path = f"/sandbox/var/repos/{self.run_id}"
        if not os.path.exists(repo_local_path):
            os.makedirs(repo_local_path)

        clone_url = urljoin(configs.vcs_host, f"{self.model_obj.repo}.git")
        repo = Repo.clone_from(url=clone_url, to_path=repo_local_path, branch=self.model_obj.branch)
        repo.head.reset(self.model_obj.commit)
        repo.head.reset("--hard")
        repo_paths = {"local": repo_local_path, "remote": repo_remote_path}
        return repo_paths

    def _delete_code(self):
        repo_local_path = f"/sandbox/var/repos/{self.run_id}"
        rmtree(repo_local_path)

        if self.model_obj.bin_release:
            temp_path = "/sandbox/var/zeroci/bin"
            temp_bin_path = os.path.join(temp_path, self.model_obj.bin_release)
            os.remove(temp_bin_path)

    def _prepare_bin_dirs(self, bin_remote_path):
        bin_name = bin_remote_path.split(os.path.sep)[-1]
        if isinstance(self.model_obj, TriggerModel):
            release = self.model_obj.commit[:7]
            local_path = os.path.join("/sandbox/var/bin/", self.model_obj.repo, self.model_obj.branch)
        else:
            release = str(datetime.fromtimestamp(self.model_obj.timestamp)).replace(" ", "_")[:16]
            local_path = os.path.join("/sandbox/var/bin/", self.model_obj.schedule_name)

        bin_release = f"{bin_name}_{release}"
        bin_local_path = os.path.join(local_path, bin_release)
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        temp_path = "/sandbox/var/zeroci/bin"
        temp_bin_path = os.path.join(temp_path, bin_release)
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        return bin_local_path, temp_bin_path

    def _get_bin(self, bin_remote_path, job_number):
        if bin_remote_path and job_number == 0:
            bin_local_path, temp_bin_path = self._prepare_bin_dirs(bin_remote_path)
            bin_release = bin_local_path.split(os.path.sep)[-1]
            cmd = f"cp {bin_remote_path} /zeroci/bin/{bin_release}"
            container.execute_command(cmd=cmd, id="", verbose=False)
            if not os.path.exists(temp_bin_path):
                return

            copyfile(temp_bin_path, bin_local_path)
            if os.path.exists(bin_local_path):
                self.model_obj.bin_release = bin_release
                self.model_obj.save()

    def _set_bin(self):
        if self.model_obj.bin_release:
            bin = self.model_obj.bin_release.split("_")[0]
            cmd = f"mkdir /opt/bin/; cp /zeroci/bin/{self.model_obj.bin_release} /opt/bin/{bin}"
            container.execute_command(cmd=cmd, id="", verbose=False)

    def build_and_test(self, id, schedule_name=None, script=None):
        """Builds, runs tests, calculates status and gives report on telegram and your version control system.
        
        :param id: DB's id of this run details.
        :type id: str
        :param schedule_name: it will have a value if the run is scheduled.
        :param schedule_name: str
        """
        self.run_id = id
        if not schedule_name:
            self.model_obj = TriggerRun.get(id=self.run_id)
            script = self._load_yaml()
        else:
            self.model_obj = SchedulerRun.get(id=self.run_id)
        if script:
            valid = self.validate_yaml(run_id=self.run_id, model_obj=self.model_obj, script=script)
            if valid:
                repo_paths = self.clone_repo()
                worked = deployed = installed = True
                for i, job in enumerate(script["jobs"]):
                    if not (worked and deployed and installed):
                        break
                    log = """
                    ******************************************************
                    Starting {job_name} job
                    ******************************************************
                    """.format(
                        job_name=job["name"]
                    ).replace(
                        "  ", ""
                    )
                    r.rpush(self.run_id, log)
                    deployed, installed = self.build(job=job, repo_paths=repo_paths, job_number=i)
                    if deployed:
                        if installed:
                            worked = self.test_run(job=job)
                            self._get_bin(bin_remote_path=job.get("bin_path"), job_number=i)
                        container.delete()
                self._delete_code()
        r.rpush(self.run_id, "hamada ok")
        self.cal_status()
        reporter.report(run_id=self.run_id, model_obj=self.model_obj, schedule_name=schedule_name)

    def schedule_run(self, job):
        """Builds, runs tests, calculates status and gives report on telegram.

        :param schedule_name: the name of the scheduled run.
        :type schedule_name: str
        :param script: the script that should run your schedule.
        :type script: str
        """
        triggered_by = job.get("triggered_by", "ZeroCI Scheduler")
        data = {
            "status": "pending",
            "timestamp": int(datetime.now().timestamp()),
            "schedule_name": job["schedule_name"],
            "triggered_by": triggered_by,
            "bin_release": None,
        }
        scheduler_run = SchedulerRun(**data)
        scheduler_run.save()
        id = str(scheduler_run.id)
        data["id"] = id
        r.publish("zeroci_status", json.dumps(data))
        self.build_and_test(id=id, schedule_name=job["schedule_name"], script=job)

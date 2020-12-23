import json
import os
import traceback
from datetime import datetime
from urllib.parse import urljoin

import requests
import yaml
from deployment.container import Container
from kubernetes.client import V1EnvVar
from models.initial_config import InitialConfig
from models.run import Run
from models.run_config import RunConfig
from packages.vcs.vcs import VCSFactory
from redis import Redis
from utils.constants import *
from utils.utils import Utils

from actions.reporter import Reporter


class Runner:
    def __init__(self, run=None, run_id=None):
        self.run_id = run_id
        self.run_obj = run
        self._redis = None
        self._container = None
        self._reporter = None
        self._utils = None

    @property
    def redis(self):
        if not self._redis:
            self._redis = Redis()
        return self._redis

    @property
    def container(self):
        if not self._container:
            self._container = Container()
        return self._container

    @property
    def reporter(self):
        if not self._reporter:
            self._reporter = Reporter()
        return self._reporter

    @property
    def utils(self):
        if not self._utils:
            self._utils = Utils()
        return self._utils

    def _test_run(self, job):
        """Runs tests and store the result in DB."""
        for line in job["script"]:
            if line.get("type") == "neph":
                finished = self._neph_run(job_name=job["name"], line=line)
            else:
                finished = self._normal_run(job_name=job["name"], line=line)
            if not finished:
                return False
        return True

    def _normal_run(self, job_name, line):
        status = SUCCESS
        response, file_path = self.container.run_test(run_id=self.run_id, run_cmd=line["cmd"])
        result = response.stdout
        type = LOG_TYPE
        if response.returncode:
            status = FAILURE
        if file_path:
            try:
                result = self.utils.xml_parse(path=file_path, line=line["cmd"])
                type = TESTSUITE_TYPE
            except:
                pass
            os.remove(file_path)

        name = "{job_name}: {test_name}".format(job_name=job_name, test_name=line["name"])
        self.run_obj.result.append({"type": type, "status": status, "name": name, "content": result})
        self.run_obj.save()
        if response.returncode in [137, 124]:
            return False
        return True

    def _neph_run(self, job_name, line):
        status = SUCCESS
        working_dir = line["working_dir"]
        yaml_path = line["yaml_path"]
        neph_id = f"{self.run_id}:{job_name}:{line['name']}"
        cmd = f"export NEPH_RUN_ID='{neph_id}' \n cd {working_dir} \n {BIN_DIR}neph -y {yaml_path} -m CI"
        response = self.container.execute_on_test_container(cmd=cmd, run_id=self.run_id)
        if response.returncode:
            status = FAILURE

        name = "{job_name}:{test_name}".format(job_name=job_name, test_name=line["name"])
        self.run_obj.result.append({"type": LOG_TYPE, "status": status, "name": name, "content": response.stdout})
        self.run_obj.save()

        for key in self.redis.keys():
            key = key.decode()
            if key.startswith(f"neph:{self.run_id}:{job_name}:{line['name']}"):
                status = SUCCESS
                logs = self.redis.lrange(key, 0, -1)
                all_logs = ""
                for log in logs:
                    log = json.loads(log.decode())
                    if log["type"] == "stderr":
                        status = FAILURE
                    all_logs += log["content"]
                name = key.split(f"neph:{self.run_id}:")[-1]
                self.run_obj.result.append({"type": LOG_TYPE, "status": status, "name": name, "content": all_logs})
                self.run_obj.save()

        if response.returncode in [137, 124]:
            return False
        return True

    def _build(self, job, clone_details, job_number):
        """Create VM with the required prerequisties and run installation steps to get it ready for running tests."""
        env = self._get_run_env()
        deployed = self.container.deploy(
            env=env, prerequisites=job["prerequisites"], repo_path=clone_details["remote_path"]
        )
        installed = False
        if deployed:
            if job_number != 0:
                self._set_bin()
            response = self.container.execute_on_helper(cmd=clone_details["cmd"])
            if response.returncode:
                name = "{job_name}: Clone Repository".format(job_name=job["name"])
                result = response.stdout
                self.redis.rpush(self.run_id, result)
            else:
                response = self.container.execute_on_test_container(cmd=job["install"], run_id=self.run_id)
                if response.returncode:
                    name = "{job_name}: Installation".format(job_name=job["name"])
                    result = response.stdout
                else:
                    installed = True
        else:
            name = "{job_name}: Deploy".format(job_name=job["name"])
            result = "Couldn't deploy a container"
            self.redis.rpush(self.run_id, result)

        if not installed:
            self.run_obj.result.append({"type": LOG_TYPE, "status": ERROR, "name": name, "content": result})
            self.run_obj.save()

        return deployed, installed

    def _cal_status(self):
        """Calculate the status of the whole tests result has been stored on the BD's id."""
        status = SUCCESS
        for result in self.run_obj.result:
            if result["status"] != SUCCESS:
                status = result["status"]
        self.run_obj.status = status
        self.run_obj.save()

    def _get_run_env(self):
        """Get run environment variables."""
        name = self.run_obj.repo
        run_config = RunConfig(name=name)
        run_env = run_config.env
        env = []
        for key in run_env.keys():
            env_var = V1EnvVar(name=key, value=run_env.get(key))
            env.append(env_var)
        return env

    def _repo_clone_details(self):
        """Clone repo."""
        configs = InitialConfig()
        repo_remote_path = os.path.join(REPOS_DIR, self.run_obj.repo)
        clone_url = urljoin(configs.vcs_host, f"{self.run_obj.repo}.git")
        cmd = """git clone {clone_url} {repo_remote_path} --branch {branch}
        cd {repo_remote_path}
        git reset --hard {commit}
        """.format(
            clone_url=clone_url,
            repo_remote_path=repo_remote_path,
            branch=self.run_obj.branch,
            commit=self.run_obj.commit,
        )
        clone_details = {"cmd": cmd, "remote_path": repo_remote_path}
        return clone_details

    def _prepare_bin_dirs(self, bin_remote_path):
        self.bin_name = bin_remote_path.split(os.path.sep)[-1]
        release = self.run_obj.commit[:7]
        local_path = os.path.join(BIN_DIR, self.run_obj.repo, self.run_obj.branch)
        bin_release = f"{self.bin_name}_{release}"
        bin_local_path = os.path.join(local_path, bin_release)
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        return bin_local_path

    def _get_bin(self, bin_remote_path, job_number):
        if bin_remote_path and not job_number:
            bin_local_path = self._prepare_bin_dirs(bin_remote_path)
            bin_release = bin_local_path.split(os.path.sep)[-1]
            bin_tmp_path = os.path.join(BIN_DIR, bin_release)
            cmd = f"cp {bin_remote_path} {bin_tmp_path}"
            self.container.execute_on_test_container(cmd=cmd, run_id="", verbose=False)
            self.container.get_remote_file_from_helper(remote_path=bin_tmp_path, local_path=bin_local_path)

            if os.path.exists(bin_local_path):
                self.run_obj.bin_release = bin_release
                self.run_obj.save()

    def _set_bin(self):
        if self.run_obj.bin_release:
            bin_local_path = self._prepare_bin_dirs(self.bin_name)
            bin_remote_path = os.path.join(BIN_DIR, self.bin_name)
            self.container.set_remote_file_on_helper(remote_path=bin_remote_path, local_path=bin_local_path)
            self.container.execute_on_helper(f"chmod +x {bin_remote_path}")

    def build_and_test(self, run_id, repo_config):
        """Builds, runs tests, calculates status and gives report on telegram and your version control system.

        :param id: DB's id of this run details.
        :type id: str
        :param schedule_name: it will have a value if the run is scheduled.
        :param schedule_name: str
        """
        self.run_id = run_id
        self.run_obj = Run.get(run_id=self.run_id)
        clone_details = self._repo_clone_details()
        worked = deployed = installed = True
        for i, job in enumerate(repo_config["jobs"]):
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
            self.redis.rpush(self.run_id, log)
            deployed, installed = self._build(job=job, clone_details=clone_details, job_number=i)
            if deployed:
                if installed:
                    worked = self._test_run(job=job)
                    self._get_bin(bin_remote_path=job.get("bin_path"), job_number=i)
                self.container.delete()
        self.redis.rpush(self.run_id, "hamada ok")
        self._cal_status()
        self.reporter.report(run_id=self.run_id, run_obj=self.run_obj)

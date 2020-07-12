import json
import os
import traceback
from datetime import datetime
from urllib.parse import urljoin

import redis
import requests
import yaml

from actions.yaml_validation import Validator
from deployment.container import Container
from kubernetes.client import V1EnvVar
from models.initial_config import InitialConfig
from models.run_config import RunConfig
from models.scheduler_run import SchedulerRun
from models.trigger_run import TriggerModel, TriggerRun
from packages.vcs.vcs import VCSFactory
from utils.reporter import Reporter
from utils.utils import Utils

container = Container()
reporter = Reporter()
utils = Utils()
r = redis.Redis()

SUCCESS = "success"
FAILURE = "failure"
ERROR = "error"
PENDING = "pending"
LOG_TYPE = "log"
TESTSUITE_TYPE = "testsuite"
NEPH_TYPE = "neph"


class Actions(Validator):
    _REPOS_DIR = "/zeroci/code/vcs_repos"
    _BIN_DIR = "/zeroci/bin/"
    run_id = None
    model_obj = None

    def test_run(self, job):
        """Runs tests and store the result in DB.
        """
        for line in job["script"]:
            if line.get("type") == "neph":
                finished = self.neph_run(job_name=job["name"], line=line)
            else:
                finished = self.normal_run(job_name=job["name"], line=line)
            if not finished:
                return False
        return True

    def normal_run(self, job_name, line):
        status = SUCCESS
        response, file_path = container.run_test(id=self.run_id, run_cmd=line["cmd"])
        result = response.stdout
        type = LOG_TYPE
        if response.returncode:
            status = FAILURE
        if file_path:
            try:
                result = utils.xml_parse(path=file_path, line=line["cmd"])
                type = TESTSUITE_TYPE
            except:
                pass
            os.remove(file_path)

        name = "{job_name}: {test_name}".format(job_name=job_name, test_name=line["name"])
        self.model_obj.result.append({"type": type, "status": status, "name": name, "content": result})
        self.model_obj.save()
        if response.returncode in [137, 124]:
            return False
        return True

    def neph_run(self, job_name, line):
        status = SUCCESS
        working_dir = line["working_dir"]
        yaml_path = line["yaml_path"]
        cmd = f"cd {working_dir} \n /zeroci/bin/neph -y {yaml_path} -m CI"
        response = container.execute_command(cmd=cmd, id=self.run_id)
        if response.returncode:
            status = FAILURE

        name = "{job_name}: {test_name}".format(job_name=job_name, test_name=line["name"])
        self.model_obj.result.append({"type": LOG_TYPE, "status": status, "name": name, "content": response.stdout})
        self.model_obj.save()
        if response.returncode in [137, 124]:
            return False

        cmd = f"ls --color=never {working_dir}/.neph"
        response = container.execute_command(cmd=cmd, id="", verbose=False)
        if response.returncode:
            result = "No logs found for neph"
            name = f"{name}: logs"
            self.model_obj.result.append({"type": LOG_TYPE, "status": status, "name": name, "content": result})
        self.model_obj.save()
        neph_jobs_names = response.stdout.split()
        for neph_job_name in neph_jobs_names:
            status = SUCCESS
            cmd = f"cat {working_dir}/.neph/{neph_job_name}/log/log.out"
            out = container.execute_command(cmd=cmd, id="", verbose=False)
            cmd = f"cat {working_dir}/.neph/{neph_job_name}/log/log.err"
            err = container.execute_command(cmd=cmd, id="", verbose=False)
            result = f"stdout:\n {out.stdout} \n\nstderr:\n {err.stdout}"
            if err.stdout:
                status = FAILURE
            name = f"{job_name}: {line['name']}: {neph_job_name}"
            self.model_obj.result.append({"type": LOG_TYPE, "status": status, "name": name, "content": result})
            self.model_obj.save()

        cmd = f"rm -r {working_dir}/.neph"
        container.execute_command(cmd=cmd, id="", verbose=False)
        return True

    def build(self, job, clone_details, job_number):
        """Create VM with the required prerequisties and run installation steps to get it ready for running tests.
        """
        env = self._get_run_env()
        deployed = container.deploy(env=env, prerequisites=job["prerequisites"], repo_path=clone_details["remote_path"])
        installed = False
        if deployed:
            if job_number != 0:
                self._set_bin()
            response = container.ssh_command(cmd=clone_details["cmd"])
            if response.returncode:
                name = "{job_name}: Clone Repository".format(job_name=job["name"])
                result = response.stdout
                r.rpush(self.run_id, result)
            else:
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

        if not installed:
            self.model_obj.result.append({"type": LOG_TYPE, "status": ERROR, "name": name, "content": result})
            self.model_obj.save()

        return deployed, installed

    def cal_status(self):
        """Calculate the status of the whole tests result has been stored on the BD's id.
        """
        status = SUCCESS
        for result in self.model_obj.result:
            if result["status"] != SUCCESS:
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
        self.model_obj.result.append({"type": LOG_TYPE, "status": ERROR, "name": "Yaml File", "content": msg})
        self.model_obj.save()
        return False

    def repo_clone_details(self):
        """Clone repo.
        """
        configs = InitialConfig()
        repo_remote_path = os.path.join(self._REPOS_DIR, self.model_obj.repo)
        clone_url = urljoin(configs.vcs_host, f"{self.model_obj.repo}.git")
        cmd = """git clone {clone_url} {repo_remote_path} --branch {branch}
        cd {repo_remote_path}
        git reset --hard {commit}
        """.format(
            clone_url=clone_url,
            repo_remote_path=repo_remote_path,
            branch=self.model_obj.branch,
            commit=self.model_obj.commit,
        )
        clone_details = {"cmd": cmd, "remote_path": repo_remote_path}
        return clone_details

    def _prepare_bin_dirs(self, bin_remote_path):
        self.bin_name = bin_remote_path.split(os.path.sep)[-1]
        if isinstance(self.model_obj, TriggerModel):
            release = self.model_obj.commit[:7]
            local_path = os.path.join(self._BIN_DIR, self.model_obj.repo, self.model_obj.branch)
        else:
            release = str(datetime.fromtimestamp(self.model_obj.timestamp)).replace(" ", "_")[:16]
            local_path = os.path.join(self._BIN_DIR, self.model_obj.schedule_name)

        bin_release = f"{self.bin_name}_{release}"
        bin_local_path = os.path.join(local_path, bin_release)
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        return bin_local_path

    def _get_bin(self, bin_remote_path, job_number):
        if bin_remote_path and job_number == 0:
            bin_local_path = self._prepare_bin_dirs(bin_remote_path)
            bin_release = bin_local_path.split(os.path.sep)[-1]
            bin_tmp_path = os.path.join(self._BIN_DIR, bin_release)
            cmd = f"cp {bin_remote_path} {bin_tmp_path}"
            container.execute_command(cmd=cmd, id="", verbose=False)
            container.ssh_get_remote_file(remote_path=bin_tmp_path, local_path=bin_local_path)

            if os.path.exists(bin_local_path):
                self.model_obj.bin_release = bin_release
                self.model_obj.save()

    def _set_bin(self):
        if self.model_obj.bin_release:
            bin_local_path = self._prepare_bin_dirs(self.bin_name)
            bin_remote_path = os.path.join(self._BIN_DIR, self.bin_name)
            container.ssh_set_remote_file(remote_path=bin_remote_path, local_path=bin_local_path)
            container.ssh_command(f"chmod +x {bin_remote_path}")

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
                clone_details = self.repo_clone_details()
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
                    deployed, installed = self.build(job=job, clone_details=clone_details, job_number=i)
                    if deployed:
                        if installed:
                            worked = self.test_run(job=job)
                            self._get_bin(bin_remote_path=job.get("bin_path"), job_number=i)
                        container.delete()
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
            "status": PENDING,
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

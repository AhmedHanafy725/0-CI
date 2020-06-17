import json
import os
import traceback
from datetime import datetime
from shutil import move, rmtree
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
from models.trigger_run import TriggerRun
from packages.vcs.vcs import VCSFactory
from utils.reporter import Reporter
from utils.utils import Utils

container = Container()
reporter = Reporter()
utils = Utils()
r = redis.Redis()


class Actions:
    _REPOS_DIR = "/opt/code/vcs_repos"
    prerequisites = None
    install_script = None
    test_script = None
    parent_model = None
    run_id = None

    def test_run(self):
        """Runs tests and store the result in DB.
        """
        model_obj = self.parent_model(id=self.run_id)
        status = "success"
        for i, line in enumerate(self.test_script):
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

            model_obj.result.append({"type": type, "status": status, "name": line["name"], "content": result})
            model_obj.save()
            if i + 1 == len(self.test_script):
                r.rpush(self.run_id, "hamada ok")
            if response.returncode in [137, 124]:
                r.rpush(self.run_id, "hamada ok")
                break

    def build(self):
        """Create VM with the required prerequisties and run installation steps to get it ready for running tests.
        """
        model_obj = self.parent_model(id=self.run_id)
        env = self._get_run_env()
        repo_paths = self.clone_repo()
        deployed = container.deploy(env=env, prerequisites=self.prerequisites, repo_paths=repo_paths)
        installed = False
        if deployed:
            response = container.execute_command(cmd=self.install_script, id=self.run_id)
            if response.returncode:
                name = "Installation"
                result = response.stdout
            else:
                installed = True
        else:
            name = "Deploy"
            result = "Couldn't deploy a container"
            r.rpush(self.run_id, result)

        if not deployed or not installed:
            r.rpush(self.run_id, "hamada ok")
            model_obj.result.append({"type": "log", "status": "error", "name": name, "content": result})
            model_obj.save()
            self.cal_status()

        return deployed, installed

    def cal_status(self):
        """Calculate the status of the whole tests result has been stored on the BD's id.
        """
        model_obj = self.parent_model(id=self.run_id)
        status = "success"
        for result in model_obj.result:
            if result["status"] != "success":
                status = result["status"]
        model_obj.status = status
        model_obj.save()

    def _get_run_env(self):
        """Get run environment variables.
        """
        model_obj = self.parent_model(id=self.run_id)
        if isinstance(model_obj, TriggerRun):
            name = model_obj.repo
        else:
            name = model_obj.schedule_name
        run_config = RunConfig.find(name=name)
        if run_config and len(run_config) == 1:
            run_config = run_config[0]
        else:
            run_config = RunConfig(name=name)

        run_env = run_config.env
        env = []
        for key in run_env.keys():
            env_var = V1EnvVar(name=key, value=run_env.get(key))
            env.append(env_var)
        return env

    def _load_yaml(self):
        model_obj = self.parent_model(id=self.run_id)
        vcs_obj = VCSFactory().get_cvn(repo=model_obj.repo)
        script = vcs_obj.get_content(ref=model_obj.commit, file_path="zeroCI.yaml")
        if script:
            try:
                return yaml.safe_load(script)
            except:
                msg = traceback.format_exc()
        else:
            msg = "zeroCI.yaml is not found on the repository's home"

        r.rpush(self.run_id, msg)
        r.rpush(self.run_id, "hamada ok")
        model_obj.result.append({"type": "log", "status": "error", "name": "Yaml File", "content": msg})
        model_obj.save()
        self.cal_status()
        return False

    def _validate_yaml(self, script):
        model_obj = self.parent_model(id=self.run_id)
        msg = ""

        if not msg:
            test_script = script.get("script")
            if not test_script:
                msg = "script should be in yaml file and shouldn't be empty"
            else:
                if not isinstance(test_script, list):
                    msg = "script should be list"
                else:
                    for item in test_script:
                        if not isinstance(item, dict):
                            msg = "Every element in script should be dict"
                        else:
                            name = item.get("name")
                            if not name:
                                msg = "Every element in script should conttain a name"
                            else:
                                if not isinstance(name, str):
                                    msg = "Eveey name in script should be str"
                            cmd = item.get("cmd")
                            if not cmd:
                                msg = "Every element in script should conttain a cmd"
                            else:
                                if not isinstance(cmd, str):
                                    msg = "Eveey cmd in script should be str"

            install_script = script.get("install")
            if not install_script:
                msg = "install should be in yaml file and shouldn't be empty"
            else:
                if not isinstance(install_script, str):
                    msg = "install should be str"

            prerequisites = script.get("prerequisites")
            if not prerequisites:
                msg = "prerequisites should be in yaml file and shouldn't be empty"
            else:
                if not isinstance(prerequisites, dict):
                    msg = "prerequisites should be dict"
                else:
                    image_name = script["prerequisites"].get("image_name")
                    if not image_name:
                        msg = "prerequisites should contain image_name and shouldn't be empty"
                    else:
                        if not isinstance(image_name, str):
                            msg = "image_name should be str"
                        else:
                            if ":" in image_name:
                                repository, tag = image_name.split(":")
                            else:
                                repository = image_name
                                tag = "latest"
                            response = requests.get(f"https://index.docker.io/v1/repositories/{repository}/tags/{tag}")
                            if response.status_code is not requests.codes.ok:
                                msg = "Invalid docker image's name "
                    
                    shell_bin = script["prerequisites"].get("shell_bin")
                    if shell_bin:
                        if not isinstance(shell_bin, str):
                            msg = "shell_bin should be str"

            bin_path = script.get("bin_path")
            if bin_path:
                if not isinstance(bin_path, str):
                    msg = "bin_path should be str"

        if msg:
            r.rpush(self.run_id, msg)
            r.rpush(self.run_id, "hamada ok")
            model_obj.result.append({"type": "log", "status": "error", "name": "Yaml File", "content": msg})
            model_obj.save()
            self.cal_status()
            return False

        self.prerequisites = prerequisites
        self.install_script = install_script
        self.test_script = test_script
        self.bin_remote_path = bin_path
        if shell_bin:
            container.shell_bin = shell_bin
        return True

    def clone_repo(self):
        """Clone repo.
        """
        configs = InitialConfig()
        model_obj = self.parent_model(id=self.run_id)
        repo_remote_path = os.path.join(self._REPOS_DIR, model_obj.repo)
        repo_local_path = f"/sandbox/var/repos/{self.run_id}"
        if not os.path.exists(repo_local_path):
            os.makedirs(repo_local_path)
        
        clone_url = urljoin(configs.vcs_host, f"{model_obj.repo}.git")
        repo = Repo.clone_from(url=clone_url, to_path=repo_local_path, branch=model_obj.branch)
        repo.head.reset(model_obj.commit)
        repo.head.reset("--hard")
        repo_paths = {"local": repo_local_path, "remote": repo_remote_path}
        return repo_paths

    def _delete_code(self):
        repo_local_path = f"/sandbox/var/repos/{self.run_id}"
        rmtree(repo_local_path)
        
    def get_bin(self):
        if self.bin_remote_path:
            model_obj = self.parent_model(id=self.run_id)
            bin_name = self.bin_remote_path.split(os.path.sep)[-1]
            if isinstance(model_obj, TriggerRun):
                release = model_obj.commit[:7]
                local_path = os.path.join("/sandbox/var/bin/", model_obj.repo, model_obj.branch)
            else:
                release = str(datetime.fromtimestamp(model_obj.timestamp)).replace(" ", "_")[:16]
                local_path = os.path.join("/sandbox/var/bin/", model_obj.schedule_name)

            bin_release = f"{bin_name}_{release}"
            temp_path = "/sandbox/var/zeroci/bin"
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)
            cmd = f"cp {self.bin_remote_path} /zeroci/bin/{bin_release}"
            container.execute_command(cmd=cmd, id="", verbose=False)

            bin_local_path = os.path.join(local_path, bin_release)
            temp_bin_path = os.path.join(temp_path, bin_release)
            if not os.path.exists(temp_bin_path):
                return

            if not os.path.exists(local_path):
                os.makedirs(local_path)

            move(temp_bin_path, bin_local_path)
            if os.path.exists(bin_local_path):
                model_obj.bin_release = bin_release
                model_obj.save()

    def build_and_test(self, id, schedule_name=None, script=None):
        """Builds, runs tests, calculates status and gives report on telegram and your version control system.
        
        :param id: DB's id of this run details.
        :type id: str
        :param schedule_name: it will have a value if the run is scheduled.
        :param schedule_name: str
        """
        self.run_id = id
        if not schedule_name:
            self.parent_model = TriggerRun
            script = self._load_yaml()

        if script:
            valid = self._validate_yaml(script)
            if valid:
                deployed, installed = self.build()
                if deployed:
                    if installed:
                        self.test_run()
                        self.cal_status()
                        self.get_bin()
                    container.delete()
                    self._delete_code()
        reporter.report(id=self.run_id, parent_model=self.parent_model, schedule_name=schedule_name)

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
            "timestamp": datetime.now().timestamp(),
            "schedule_name": job["schedule_name"],
            "triggered_by": triggered_by,
            "bin_release": None,
        }
        scheduler_run = SchedulerRun(**data)
        scheduler_run.save()
        id = str(scheduler_run.id)
        data["id"] = id
        r.publish("zeroci_status", json.dumps(data))
        self.parent_model = SchedulerRun
        self.build_and_test(id=id, schedule_name=job["schedule_name"], script=job)

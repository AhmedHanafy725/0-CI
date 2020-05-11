import json
import os
import traceback
from datetime import datetime

import redis
import requests
import yaml

from deployment.container import Container
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
    clone_script = None
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
        deployed = container.deploy(env=env, prerequisites=self.prerequisites)
        installed = False
        if deployed:
            response = container.install_app(
                id=self.run_id, install_script=self.install_script, clone_script=self.clone_script
            )
            if response.returncode:
                name = "Installation"
                result = response.stdout
                r.rpush(self.run_id, "hamada ok")
            else:
                installed = True
        else:
            name = "Deploy"
            result = "Couldn't deploy a container"

        if not deployed or not installed:
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
                    image_name = script["prerequisites"].get("imageName")
                    if not image_name:
                        msg = "prerequisites should contain imageName and shouldn't be empty"
                    else:
                        if not isinstance(image_name, str):
                            msg = "imageName should be str"
                        else:
                            if ":" in image_name:
                                repository, tag = image_name.split(":")
                            else:
                                repository = image_name
                                tag = "latest"
                            r = requests.get(f"https://index.docker.io/v1/repositories/{repository}/tags/{tag}")
                            if r.status_code is not requests.codes.ok:
                                msg = "Invalid docker image's name "

        if msg:
            model_obj.result.append({"type": "log", "status": "error", "name": "Yaml File", "content": msg})
            model_obj.save()
            self.cal_status()
            return False

        self.prerequisites = prerequisites
        self.install_script = install_script
        self.test_script = test_script
        return True

    def _set_clone_script(self):
        """Read zeroCI yaml script from the repo home directory and divide it to prerequisites and (install and test) scripts.
        """
        configs = InitialConfig()
        model_obj = self.parent_model(id=self.run_id)
        org_repo_name = model_obj.repo.split("/")[0]
        self.clone_script = """apt-get update
        apt-get install -y git
        mkdir -p {repos_dir}/{org_repo_name}
        cd {repos_dir}/{org_repo_name}
        git clone {vcs_host}/{repo}.git --branch {branch}
        cd {repos_dir}/{repo}
        git reset --hard {commit}
        """.format(
            repos_dir=self._REPOS_DIR,
            repo=model_obj.repo,
            branch=model_obj.branch,
            commit=model_obj.commit,
            org_repo_name=org_repo_name,
            vcs_host=configs.vcs_host,
        )

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
            self._set_clone_script()
            script = self._load_yaml()

        if script:
            valid = self._validate_yaml(script)
            if valid:
                deployed, installed = self.build()
                if deployed:
                    if installed:
                        self.test_run()
                        self.cal_status()
                    container.delete()
        reporter.report(id=self.run_id, parent_model=self.parent_model, schedule_name=schedule_name)

    def schedule_run(self, schedule_name, script):
        """Builds, runs tests, calculates status and gives report on telegram.

        :param schedule_name: the name of the scheduled run.
        :type schedule_name: str
        :param script: the script that should run your schedule.
        :type script: str
        """
        data = {"status": "pending", "timestamp": datetime.now().timestamp(), "schedule_name": schedule_name}
        scheduler_run = SchedulerRun(**data)
        scheduler_run.save()
        id = str(scheduler_run.id)
        data["id"] = id
        r.publish(schedule_name, json.dumps(data))
        self.parent_model = SchedulerRun
        self.build_and_test(id=id, schedule_name=schedule_name, script=script)

import json
import os
from datetime import datetime

import redis
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
configs = InitialConfig()
r = redis.Redis()


class Actions:
    _REPOS_DIR = "/opt/code/vcs_repos"
    prequisties = None
    install_script = None
    test_script = None
    parent_model = None
    run_id = None

    def test_run(self):
        """Runs tests and store the result in DB.
        """
        model_obj = self.parent_model(id=self.run_id)
        status = "success"
        if self.test_script:
            for i, line in enumerate(self.test_script):
                status = "success"
                if line.startswith("#"):
                    continue
                response, file_path = container.run_test(id=self.run_id, run_cmd=line)
                if file_path:
                    if response.returncode:
                        status = "failure"
                    try:
                        result = utils.xml_parse(path=file_path, line=line)
                        model_obj.result.append(
                            {
                                "type": "testsuite",
                                "status": status,
                                "name": result["summary"]["name"],
                                "content": result,
                            }
                        )
                    except:
                        model_obj.result.append(
                            {"type": "log", "status": status, "name": line, "content": response.stdout}
                        )
                    os.remove(file_path)
                else:
                    if response.returncode:
                        status = "failure"
                    model_obj.result.append({"type": "log", "status": status, "name": line, "content": response.stdout})
                model_obj.save()
                if i + 1 == len(self.test_script):
                    r.rpush(self.run_id, "hamada ok")
        else:
            r.rpush(self.run_id, "hamada ok")
            model_obj.result.append({"type": "log", "status": status, "name": "No tests", "content": "No tests found"})
            model_obj.save()

    def build(self):
        """Create VM with the required prerequisties and run installation steps to get it ready for running tests.
        """
        model_obj = self.parent_model(id=self.run_id)
        if self.install_script:
            env = self._get_run_env()
            deployed = container.deploy(env=env, prequisties=self.prequisties)
            if deployed:
                response = container.install_app(id=self.run_id, install_script=self.install_script)
                if response.returncode:
                    model_obj.result.append(
                        {"type": "log", "status": "error", "name": "Installation", "content": response.stdout}
                    )
                    model_obj.save()
                    r.rpush(self.run_id, "hamada ok")
                    self.cal_status()
                return deployed, response

            else:
                model_obj.result.append(
                    {"type": "log", "status": "error", "name": "Deploy", "content": "Couldn't deploy a vm"}
                )
                model_obj.save()
                self.cal_status()
        else:
            model_obj.result.append(
                {"type": "log", "status": "error", "name": "ZeroCI", "content": "Didn't find something to install"}
            )
            model_obj.save()
            self.cal_status()

        return None, None

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

    def _install_test_scripts(self):
        """Read zeroCI yaml script from the repo home directory and divide it to prequisties and (install and test) scripts.
        """
        trigger_run = TriggerRun(id=self.run_id)
        org_repo_name = trigger_run.repo.split("/")[0]
        clone = """apt-get update &&
        apt-get install -y git &&
        mkdir -p {repos_dir}/{org_repo_name} &&
        cd {repos_dir}/{org_repo_name} &&
        git clone {vcs_host}/{repo}.git --branch {branch} &&
        cd {repos_dir}/{repo} &&
        git reset --hard {commit} &&
        """.format(
            repos_dir=self._REPOS_DIR,
            repo=trigger_run.repo,
            branch=trigger_run.branch,
            commit=trigger_run.commit,
            org_repo_name=org_repo_name,
            vcs_host=configs.vcs_host,
        ).replace(
            "\n", " "
        )

        VCSObject = VCSFactory().get_cvn(repo=trigger_run.repo)
        script = VCSObject.get_content(ref=trigger_run.commit, file_path="zeroCI.yaml")
        if script:
            yaml_script = yaml.load(script)
            self.prequisties = yaml_script.get("prequisties")
            install = " && ".join(yaml_script.get("install"))
            self.install_script = clone + install
            self.test_script = yaml_script.get("script")

    def build_and_test(self, id, schedule_name=None):
        """Builds, runs tests, calculates status and gives report on telegram and your version control system.
        
        :param id: DB's id of this run details.
        :type id: str
        :param schedule_name: it will have a value if the run is scheduled.
        :param schedule_name: str
        """
        self.run_id = id
        if not schedule_name:
            self._install_test_scripts()
            self.parent_model = TriggerRun

        deployed, response = self.build()
        if deployed:
            if not response.returncode:
                self.test_run()
                self.cal_status()
            container.delete()
        reporter.report(id=self.run_id, parent_model=self.parent_model, schedule_name=schedule_name)

    def schedule_run(self, schedule_name, install_script, test_script, prequisties):
        """Builds, runs tests, calculates status and gives report on telegram.

        :param schedule_name: the name of the scheduled run.
        :type schedule_name: str
        :param install_script: the script that should run to build your schedule.
        :type install_script: str
        :param test_script: the script that should run the tests.
        :type test_script: list
        :param prequisties: requires needed in VM.
        :type prequisties: str
        """
        data = {"status": "pending", "timestamp": datetime.now().timestamp(), "schedule_name": schedule_name}
        scheduler_run = SchedulerRun(**data)
        scheduler_run.save()
        id = str(scheduler_run.id)
        data["id"] = id
        r.publish(schedule_name, json.dumps(data))
        self.parent_model = SchedulerRun
        self.prequisties = prequisties
        self.install_script = install_script
        self.test_script = test_script
        self.build_and_test(id=id, schedule_name=schedule_name)

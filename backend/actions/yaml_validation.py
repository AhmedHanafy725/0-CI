import requests
from redis import Redis

redis = Redis()
ERROR = "error"
LOG_TYPE = "log"


class Validator:
    def _validate_test_script(self, test_script):
        msg = ""
        if not test_script:
            msg = "script should be in job file and shouldn't be empty"
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
                                msg = "Every name in script should be str"
                        cmd = item.get("cmd")
                        if not cmd:
                            type = item.get("type")
                            if not type:
                                msg = "Every element in script should conttain a cmd or type"
                            else:
                                if type == "neph":
                                    working_dir = item.get("working_dir")
                                    if not working_dir:
                                        msg = "working_dir should be added for neph type"
                                    yaml_path = item.get("yaml_path")
                                    if not yaml_path:
                                        msg = "yaml_path should be added for neph type"
                                else:
                                    msg = f"{type} is not supported"
                        else:
                            if not isinstance(cmd, str):
                                msg = "Every cmd in script should be str"
        return msg

    def _validate_install_script(self, install_script):
        msg = ""
        if not install_script:
            msg = "install should be in job file and shouldn't be empty"
        else:
            if not isinstance(install_script, str):
                msg = "install should be str"

        return msg

    def _validate_prerequisites(self, prerequisites):
        msg = ""
        if not prerequisites:
            msg = "prerequisites should be in job file and shouldn't be empty"
        else:
            if not isinstance(prerequisites, dict):
                msg = "prerequisites should be dict"
            else:
                image_name = prerequisites.get("image_name")
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
                shell_bin = prerequisites.get("shell_bin")
                if shell_bin:
                    if not isinstance(shell_bin, str):
                        msg = "shell_bin should be str"
        return msg

    def _validate_bin_path(self, bin_path):
        msg = ""
        if bin_path:
            if not isinstance(bin_path, str):
                msg = "bin_path should be str"

        return msg

    def _validate_job_name(self, name):
        msg = ""
        if not name:
            msg = "name should be in job file and shouldn't be empty"
        else:
            if not isinstance(name, str):
                msg = "name of the job should be str"

        return msg

    def _report(self, run_id, model_obj, msg):
        msg = f"{msg} (see examples: https://github.com/threefoldtech/zeroCI/tree/development/docs/config)"
        redis.rpush(run_id, msg)
        model_obj.result.append({"type": LOG_TYPE, "status": ERROR, "name": "Yaml File", "content": msg})
        model_obj.save()

    def _validate_job(self, job):
        job_name = job.get("name")
        msg = self._validate_job_name(job_name)
        if msg:
            return msg

        bin_path = job.get("bin_path")
        msg = self._validate_bin_path(bin_path)
        if msg:
            return msg

        test_script = job.get("script")
        msg = self._validate_test_script(test_script)
        if msg:
            return msg

        install_script = job.get("install")
        msg = self._validate_install_script(install_script)
        if msg:
            return msg

        prerequisites = job.get("prerequisites")
        msg = self._validate_prerequisites(prerequisites)
        return msg

    def validate_yaml(self, run_id, model_obj, script):
        jobs = script.get("jobs")
        if not jobs:
            msg = "jobs should be in yaml and shouldn't be empty"
        else:
            if not isinstance(jobs, list):
                msg = "jobs should be list"
            else:
                if len(jobs) > 3:
                    msg = "jobs shouldn't be more than 3"
                else:
                    for job in jobs:
                        msg = self._validate_job(job)
                        if msg:
                            break
        if msg:
            self._report(run_id=run_id, model_obj=model_obj, msg=msg)
            return False
        return True

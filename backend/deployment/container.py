import os
import random
import time

import redis
import yaml

from kubernetes import client, config
from kubernetes.stream import stream
from utils.utils import Utils

TIMEOUT = 120
RETRIES = 5


class Complete_Executuion:
    returncode = None
    stdout = None

    def __init__(self, rc, out):
        self.returncode = rc
        self.stdout = out


class Container(Utils):
    def __init__(self):
        super().__init__()
        self.shell_bin = "/bin/sh"

    def redis_push(self, id, content, verbose=True):
        if verbose:
            r = redis.Redis()
            r.rpush(id, content)

    def execute_command(self, cmd, id, verbose=True):
        """Execute a command on a remote machine using ssh.

        :param cmd: command to be executed on a remote machine.
        :type cmd: str
        :return: subprocess object containing (returncode, stdout)
        """
        if self.shell_bin in ["/bin/bash", "/bin/sh"]:
            command = [self.shell_bin, "-ce", cmd]
        else:
            command = [self.shell_bin, cmd]
        out = ""
        rc = None
        try:
            response = stream(
                self.client.connect_get_namespaced_pod_exec,
                name=self.name,
                namespace=self.namespace,
                command=command,
                stderr=True,
                stdin=True,
                stdout=True,
                tty=True,
                _preload_content=False,
            )
        except:
            out += "Couldn't run on the testing container, container become unreachable"
            self.redis_push(id, out, verbose=verbose)
            rc = 137
            return Complete_Executuion(rc, out)

        while response.is_open():
            start = time.time()
            try:
                content = response.read_stdout(timeout=600)
            except:
                msg = "\nConnectionError: Couldn't execute cmd on the runner"
                self.redis_push(id, msg, verbose=verbose)
                out += msg
                rc = 124
                break
            end = time.time()
            time_taken = end - start
            if content:
                self.redis_push(id, content, verbose=verbose)
                out += content
            elif time_taken > 590:
                msg = "\nTimeout exceeded 10 mins with no output"
                self.redis_push(id, msg, verbose=verbose)
                out += msg
                rc = 124
                response.close()
                break

        if not rc:
            rc = response.returncode
        if rc == 137:
            msg = "Runner expired (job takes more than 1 hour)"
            self.redis_push(id, msg, verbose=verbose)
            out += msg

        return Complete_Executuion(rc, out)

    def get_remote_file(self, remote_path, local_path):
        response = self.execute_command(f"cat {remote_path}", id="", verbose=False)
        if not response.returncode:
            self.write_file(text=response.stdout, file_path=local_path)
            return True
        return False

    def get_zeroci_node(self):
        pods = self.client.list_namespaced_pod(self.namespace)
        for pod in pods.items:
            if "zeroci" in pod.metadata.name:
                return pod.spec.node_name

    def create_pod(self, env, prerequisites, repo_paths):
        # zeroci vol
        zeroci_host_path = {"path": "/sandbox/var/zeroci"}
        zeroci_mount_path = "/zeroci"
        zeroci_vol_name = "zeroci-path"
        zeroci_vol = client.V1Volume(name=zeroci_vol_name, host_path=zeroci_host_path)
        zeroci_vol_mount = client.V1VolumeMount(mount_path=zeroci_mount_path, name=zeroci_vol_name)
        # repo vol
        repo_host_path = {"path": repo_paths["local"]}
        repo_mount_path = repo_paths["remote"]
        repo_vol_name = "repo-path"
        repo_vol = client.V1Volume(name=repo_vol_name, host_path=repo_host_path)
        repo_vol_mount = client.V1VolumeMount(mount_path=repo_mount_path, name=repo_vol_name)

        vol_mounts = [zeroci_vol_mount, repo_vol_mount]
        vols = [zeroci_vol, repo_vol]
        ports = client.V1ContainerPort(container_port=22)
        env.append(client.V1EnvVar(name="DEBIAN_FRONTEND", value="noninteractive"))
        if self.shell_bin in ["/bin/bash", "/bin/sh"]:
            commands = [self.shell_bin, "-ce", "env | grep _ >> /etc/environment && sleep 3600"]
        else:
            commands = [self.shell_bin, "env | grep _ >> /etc/environment && sleep 3600"]

        limits = {"memory": "200Mi"}
        requests = {"memory": "150Mi"}
        resources = client.V1ResourceRequirements(limits=limits, requests=requests)
        container = client.V1Container(
            name=self.name,
            image=prerequisites["image_name"],
            command=commands,
            env=env,
            ports=[ports],
            volume_mounts=vol_mounts,
            resources=resources,
        )
        zeroci_node = self.get_zeroci_node()
        spec = client.V1PodSpec(
            volumes=vols, containers=[container], hostname=self.name, restart_policy="Never", node_name=zeroci_node
        )
        meta = client.V1ObjectMeta(name=self.name, namespace=self.namespace, labels={"app": self.name})
        pod = client.V1Pod(api_version="v1", kind="Pod", metadata=meta, spec=spec)
        self.client.create_namespaced_pod(body=pod, namespace=self.namespace)

    def deploy(self, env, prerequisites, repo_paths):
        """Deploy a container on kubernetes cluster.

        :param prerequisites: list of prerequisites needed.
        :type prerequisites: list
        :return: bool (True: if virtual machine is created).
        """
        config.load_incluster_config()
        self.client = client.CoreV1Api()
        self.name = self.random_string()
        self.namespace = "default"
        if prerequisites.get("shell_bin"):
            self.shell_bin = prerequisites["shell_bin"]
        for _ in range(RETRIES):
            try:
                self.create_pod(env=env, prerequisites=prerequisites, repo_paths=repo_paths)
                self.wait_for_container()
                break
            except:
                self.delete()
        else:
            return False
        return True

    def wait_for_container(self):
        for _ in range(TIMEOUT):
            time.sleep(1)
            container_status = self.client.read_namespaced_pod_status(namespace=self.namespace, name=self.name)
            status = container_status.status.container_statuses[0]
            if status.ready:
                time.sleep(5)
                break

    def delete(self):
        """Delete the container after finishing test.
        """
        try:
            self.client.delete_namespaced_pod(name=self.name, namespace=self.namespace)
        except:
            pass

    def run_test(self, run_cmd, id):
        """Run test command and get the result as xml file if the running command is following junit otherwise result will be log.

        :param run_cmd: test command to be run.
        :type run_cmd: str
        :param id: DB's id of this run details.
        :type id: str
        :param env: environment variables needed in running tests.
        :type env: dict
        :return: path to xml file if exist and subprocess object containing (returncode, stdout, stderr)
        """
        response = self.execute_command(run_cmd, id=id)
        file_path = "/var/zeroci/{}.xml".format(self.random_string())
        remote_path = "/test.xml"
        copied = self.get_remote_file(remote_path=remote_path, local_path=file_path)
        if copied:
            file_path = file_path
            delete_cmd = f"rm -f {remote_path}"
            self.execute_command(delete_cmd, id=id)
        else:
            if os.path.exists(file_path):
                os.remove(file_path)
            file_path = None
        return response, file_path

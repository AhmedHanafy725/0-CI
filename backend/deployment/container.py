import os
import random
import time

import paramiko
import yaml
from kubernetes import client, config
from kubernetes.stream import stream
from redis import Redis
from utils.constants import BIN_DIR
from utils.utils import Utils

TIMEOUT = 120
RETRIES = 5


class Complete_Execution:
    returncode = None
    stdout = None

    def __init__(self, rc, out):
        self.returncode = rc
        self.stdout = out


class Container(Utils):
    def __init__(self, name=None, test_container_name=None, helper_container_name=None, namespace=None):
        super().__init__()
        config.load_incluster_config()
        self.shell_bin = "/bin/sh"
        self.name = name
        self.test_container_name = test_container_name
        self.helper_container_name = helper_container_name
        self.namespace = namespace
        self._redis = None
        self._client = None

    @property
    def redis(self):
        if not self._redis:
            self._redis = Redis()
        return self._redis

    @property
    def client(self):
        if not self._client:
            self._client = client.CoreV1Api()
        return self._client

    def execute_on_helper(self, cmd):
        """Execute a command on a remote machine using ssh.
        :param cmd: command to be executed on a remote machine.
        :type cmd: str
        :param ip: machine's ip.
        :type ip: str
        :param port: machine's ssh port.
        :type port: int
        :return: Execution object containing (returncode, stdout)
        """
        out = ""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        try:
            client.connect(hostname=self.name, port=22, timeout=30)
        except:
            out = "Couldn't ssh on the helper container, maybe the test broke the ssh or the helper container become unreachable"
            rc = 1
            return Complete_Execution(rc, out)
        _, stdout, _ = client.exec_command(cmd, timeout=600, get_pty=True)
        while not stdout.channel.exit_status_ready():
            try:
                output = stdout.readline()
                out += output
            except:
                msg = "Timeout Exceeded 10 mins"
                out += msg
                stdout.channel.close()
        rc = stdout.channel.recv_exit_status()

        return Complete_Execution(rc, out)

    def get_remote_file_from_helper(self, remote_path, local_path):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        client.connect(hostname=self.name, port=22, timeout=30)
        ftp = client.open_sftp()
        try:
            ftp.get(remote_path, local_path)
            ftp.close()
            return True
        except:
            return False

    def set_remote_file_on_helper(self, remote_path, local_path):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        client.connect(hostname=self.name, port=22, timeout=30)
        ftp = client.open_sftp()
        try:
            ftp.put(local_path, remote_path)
            ftp.close()
            return True
        except:
            return False

    def _redis_push(self, run_id, content, verbose=True):
        if verbose:
            self.redis.rpush(run_id, content)

    def execute_on_test_container(self, cmd, run_id, verbose=True):
        """Execute a command on a remote machine using ssh.

        :param cmd: command to be executed on a remote machine.
        :type cmd: str
        :return: Execution object containing (returncode, stdout)
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
                container=self.test_container_name,
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
            self._redis_push(run_id, out, verbose=verbose)
            rc = 137
            return Complete_Execution(rc, out)

        while response.is_open():
            start = time.time()
            try:
                content = response.read_stdout(timeout=600)
            except:
                msg = "\nConnectionError: Couldn't execute cmd on the runner"
                self._redis_push(run_id, msg, verbose=verbose)
                out += msg
                rc = 124
                break
            end = time.time()
            time_taken = end - start
            if content:
                self._redis_push(run_id, content, verbose=verbose)
                out += content
            elif time_taken > 590:
                msg = "\nTimeout exceeded 10 mins with no output"
                self._redis_push(run_id, msg, verbose=verbose)
                out += msg
                rc = 124
                response.close()
                break

        if not rc:
            rc = response.returncode
        if rc == 137:
            msg = "Runner expired (job takes more than 1 hour)"
            self._redis_push(run_id, msg, verbose=verbose)
            out += msg

        return Complete_Execution(rc, out)

    def get_remote_file_from_test_container(self, remote_path, local_path):
        response = self.execute_on_test_container(f"cat {remote_path}", run_id="", verbose=False)
        if not response.returncode:
            self.write_file(text=response.stdout, file_path=local_path)
            return True
        return False

    def _create_pod(self, env, prerequisites, repo_path):
        # zeroci vol
        bin_mount_path = BIN_DIR
        bin_vol_name = "bin-path"
        bin_vol = client.V1Volume(name=bin_vol_name, empty_dir={})
        bin_vol_mount = client.V1VolumeMount(mount_path=bin_mount_path, name=bin_vol_name)
        # repo vol
        repo_mount_path = repo_path
        repo_vol_name = "repo-path"
        repo_vol = client.V1Volume(name=repo_vol_name, empty_dir={})
        repo_vol_mount = client.V1VolumeMount(mount_path=repo_mount_path, name=repo_vol_name)

        vol_mounts = [bin_vol_mount, repo_vol_mount]
        vols = [bin_vol, repo_vol]
        ports = client.V1ContainerPort(container_port=22)
        non_interactive = client.V1EnvVar(name="DEBIAN_FRONTEND", value="noninteractive")
        redis_server = os.environ.get("REDIS", "redis")
        redis_server = client.V1EnvVar(name="NEPH_REDIS", value=f"redis://{redis_server}:6379")
        env.extend([non_interactive, redis_server])
        if self.shell_bin in ["/bin/bash", "/bin/sh"]:
            commands = [self.shell_bin, "-ce", "env | grep _ >> /etc/environment && sleep 3600"]
        else:
            commands = [self.shell_bin, "env | grep _ >> /etc/environment && sleep 3600"]

        limits = {"memory": "2000Mi"}
        requests = {"memory": "300Mi"}
        resources = client.V1ResourceRequirements(limits=limits, requests=requests)
        test_container = client.V1Container(
            name=self.test_container_name,
            image=prerequisites["image_name"],
            command=commands,
            env=env,
            volume_mounts=vol_mounts,
            resources=resources,
        )
        ssh_key = self.load_ssh_key()
        limits = {"memory": "300Mi"}
        requests = {"memory": "150Mi"}
        resources = client.V1ResourceRequirements(limits=limits, requests=requests)
        helper_container = client.V1Container(
            name=self.helper_container_name,
            image="ahmedhanafy725/ubuntu",
            command=[
                "/bin/sh",
                "-ce",
                f"echo {ssh_key} > /root/.ssh/authorized_keys && cp /usr/local/bin/* {BIN_DIR} \
                && service ssh start && sleep 3600",
            ],
            env=[non_interactive],
            ports=[ports],
            volume_mounts=vol_mounts,
            resources=resources,
        )
        spec = client.V1PodSpec(
            volumes=vols,
            containers=[test_container, helper_container],
            hostname=self.name,
            restart_policy="Never",
        )
        meta = client.V1ObjectMeta(name=self.name, namespace=self.namespace, labels={"app": self.name})
        pod = client.V1Pod(api_version="v1", kind="Pod", metadata=meta, spec=spec)
        self.client.create_namespaced_pod(body=pod, namespace=self.namespace)

    def _create_service(self):
        port = client.V1ServicePort(name="ssh", port=22)
        spec = client.V1ServiceSpec(ports=[port], selector={"app": self.name})
        meta = client.V1ObjectMeta(name=self.name, namespace=self.namespace, labels={"app": self.name})
        service = client.V1Service(api_version="v1", kind="Service", metadata=meta, spec=spec)
        self.client.create_namespaced_service(body=service, namespace=self.namespace)

    def deploy(self, env, prerequisites, repo_path):
        """Deploy a container on kubernetes cluster.

        :param prerequisites: list of prerequisites needed.
        :type prerequisites: list
        :return: bool (True: if virtual machine is created).
        """
        self.name = self.random_string()
        self.test_container_name = f"test-{self.name}"
        self.helper_container_name = f"helper-{self.name}"
        self.namespace = os.environ.get("NAMESPACE", "default")
        if prerequisites.get("shell_bin"):
            self.shell_bin = prerequisites["shell_bin"]
        for _ in range(RETRIES):
            try:
                self._create_pod(env=env, prerequisites=prerequisites, repo_path=repo_path)
                self._create_service()
                self._wait_for_container()
                break
            except:
                self.delete()
        else:
            return False
        return True

    def _wait_for_container(self):
        for _ in range(TIMEOUT):
            time.sleep(1)
            container_status = self.client.read_namespaced_pod_status(namespace=self.namespace, name=self.name)
            status = container_status.status.container_statuses[0]
            if status.ready:
                time.sleep(5)
                break

    def delete(self):
        """Delete the container after finishing test."""
        try:
            self.client.delete_namespaced_pod(name=self.name, namespace=self.namespace)
            self.client.delete_namespaced_service(name=self.name, namespace=self.namespace)
        except:
            pass

    def run_test(self, run_cmd, run_id):
        """Run test command and get the result as xml file if the running command is following junit otherwise result will be log.

        :param run_cmd: test command to be run.
        :type run_cmd: str
        :param id: DB's id of this run details.
        :type id: str
        :param env: environment variables needed in running tests.
        :type env: dict
        :return: path to xml file if exist and subprocess object containing (returncode, stdout, stderr)
        """
        response = self.execute_on_test_container(run_cmd, run_id=run_id)
        file_path = "/zeroci/xml/{}.xml".format(self.random_string())
        remote_path = "/test.xml"
        copied = self.get_remote_file_from_test_container(remote_path=remote_path, local_path=file_path)
        if copied:
            file_path = file_path
            delete_cmd = f"rm -f {remote_path}"
            self.execute_on_test_container(delete_cmd, run_id=run_id)
        else:
            if os.path.exists(file_path):
                os.remove(file_path)
            file_path = None
        return response, file_path

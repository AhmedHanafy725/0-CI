import os
import random
import time
import yaml

import paramiko
import redis

from kubernetes import client, config
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
        self.node = None

    def execute_command(self, cmd, id, ip, port=22, environment={}):
        """Execute a command on a remote machine using ssh.

        :param cmd: command to be executed on a remote machine.
        :type cmd: str
        :param ip: machine's ip.
        :type ip: str
        :param port: machine's ssh port.
        :type port: int
        :return: subprocess object containing (returncode, stdout)
        """
        r = redis.Redis()
        out = ""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        try:
            client.connect(hostname=ip, port=port, timeout=30)
        except:
            out = "Couldn't ssh on the testing VM, maybe the test broke the ssh or the VM become unreachable"
            r.rpush("5", out)
            rc = 1
            return Complete_Executuion(rc, out)
        _, stdout, _ = client.exec_command(cmd, timeout=600, environment=environment, get_pty=True)
        while not stdout.channel.exit_status_ready():
            try:
                output = stdout.readline()
                r.rpush(id, output)
                out += output
            except:
                msg = "Timeout Exceeded 10 mins"
                r.rpush("5", msg)
                out += msg
                stdout.channel.close()
        rc = stdout.channel.recv_exit_status()

        return Complete_Executuion(rc, out)

    def get_remote_file(self, remote_path, local_path, ip, port=22):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        client.connect(hostname=ip, port=port, timeout=30)
        ftp = client.open_sftp()
        try:
            ftp.get(remote_path, local_path)
            return True
        except:
            return False

    def prepare(self, prequisties):
        """Prepare the machine's parameters before creating it depend on the prequisties needed.

        :param prequisties: list of prequisties needed.
        :type prequisties: list
        """
        if "jsx" in prequisties:
            self.image_name = "ahmedhanafy725/jsx"
        else:
            self.image_name = "ahmedhanafy725/ubuntu"

    def create_pod(self, env):
        host_path = {"path": "/home/rancher/.ssh/id_rsa.pub", "type": "File"}
        mount_path = "/root/.ssh/authorized_keys"
        vol_name = "zeroci-pub-key"

        vol_mount = client.V1VolumeMount(mount_path=mount_path, name=vol_name, read_only=True)
        ports = client.V1ContainerPort(container_port=22)
        env.append(client.V1EnvVar(name="DEBIAN_FRONTEND", value="noninteractive"))
        commands = ["/bin/bash", "-ce", "env | grep _ >> /etc/environment && service ssh restart && tail -f /dev/null"]
        container = client.V1Container(
            name=self.name, image=self.image_name, command=commands, env=env, ports=[ports], volume_mounts=[vol_mount]
        )
        vol = client.V1Volume(name=vol_name, host_path=host_path)

        spec = client.V1PodSpec(volumes=[vol], containers=[container], hostname=self.name)
        meta = client.V1ObjectMeta(name=self.name, namespace=self.namespace, labels={"app": self.name})
        pod = client.V1Pod(api_version="v1", kind="Pod", metadata=meta, spec=spec)
        self.client.create_namespaced_pod(body=pod, namespace=self.namespace)

    def create_service(self):
        port = client.V1ServicePort(name="ssh", port=22)
        spec = client.V1ServiceSpec(ports=[port], selector={"app": self.name})
        meta = client.V1ObjectMeta(name=self.name, namespace=self.namespace, labels={"app": self.name})
        service = client.V1Service(api_version="v1", kind="Service", metadata=meta, spec=spec)
        self.client.create_namespaced_service(body=service, namespace=self.namespace)

    def deploy(self, env, prequisties=""):
        """Deploy a container on kubernetes cluster.

        :param prequisties: list of prequisties needed.
        :type prequisties: list
        :return: bool (True: if virtual machine is created).
        """
        self.prepare(prequisties=prequisties)
        config.load_incluster_config()
        self.client = client.CoreV1Api()
        self.name = self.random_string()
        self.namespace = "default"
        for _ in range(RETRIES):
            try:    
                self.create_pod(env=env)
                self.create_service()
                self.wait_for_container()
                break
            except:
                self.delete()
        else:
            return False
        return True 

    def wait_for_container(self):
        time.sleep(5)
        for _ in range(TIMEOUT):
            container_status = self.client.read_namespaced_pod_status(namespace=self.namespace, name=self.name)
            status = container_status.status.container_statuses[0]
            if status.ready:
                break

    def delete(self):
        """Delete the container after finishing test.
        """
        try:
            self.client.delete_namespaced_pod(name=self.name, namespace=self.namespace)
            self.client.delete_namespaced_service(name=self.name, namespace=self.namespace)
        except:
            pass

    def install_app(self, id, install_script):
        """Install application to be tested.

        :param id: DB's id of this run details.
        :type id: str
        :param install_script: bash script to install script
        :type install_script: str
        :param env: environment variables needed in the installation.
        :type env: dict
        """
        prepare_script = self.prepare_script()
        script = prepare_script + install_script
        response = self.execute_command(cmd=script, id=id, ip=self.name)
        return response

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
        response = self.execute_command(run_cmd, id=id, ip=self.name)
        file_path = "/var/zeroci/{}.xml".format(self.random_string())
        remote_path = "/test.xml"
        copied = self.get_remote_file(ip=self.name, remote_path=remote_path, local_path=file_path)
        if copied:
            file_path = file_path
            delete_cmd = f"rm -f {remote_path}"
            self.execute_command(delete_cmd, id=id, ip=self.name)
        else:
            if os.path.exists(file_path):
                os.remove(file_path)
            file_path = None
        return response, file_path

    def prepare_script(self):
        return """apt-get update &&
        apt-get install -y git python3.6 python3-pip software-properties-common &&
        pip3 install black==19.10b0 &&
        """

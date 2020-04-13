import os
import random
import time
import yaml

import paramiko
import redis

from kubernetes import client, config
from utils.utils import Utils

TIMEOUT=120

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

    def load_template(self, name):
        content = self.load_file(f"deployment/kube_templates/{name}")
        content = content.replace("appname", self.container_name)
        body_text = content.replace("image_name", self.image_name)
        body_yaml = yaml.safe_load(body_text)
        return body_yaml

    def deploy(self, prequisties=""):
        """Deploy a container on kubernetes cluster.

        :param prequisties: list of prequisties needed.
        :type prequisties: list
        :return: bool (True: if virtual machine is created).
        """
        self.prepare(prequisties=prequisties)
        config.load_incluster_config()
        self.client = client.CoreV1Api()
        self.container_name = self.random_string()

        # create pod 
        pod = self.load_template("pod.yaml")
        self.client.create_namespaced_pod(body=pod, namespace="default")

        #create service
        service = self.load_template("service.yaml")
        self.client.create_namespaced_service(body=service, namespace="default")

        self.wait_for_container()

    def wait_for_container(self):
        time.sleep(5)
        for _ in range(TIMEOUT):
            container_status = self.client.read_namespaced_pod_status(namespace="default", name=self.container_name)
            status = container_status.status.container_statuses[0]
            if status.ready:
                break

    def delete(self):
        """Delete the container after finishing test.
        """
        self.client.delete_namespaced_pod(name=self.container_name, namespace="default")
        self.client.delete_namespaced_service(name=self.container_name, namespace="default")

    def install_app(self, id, install_script, env={}):
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
        response = self.execute_command(cmd=script, id=id, ip=self.container_name, environment=env)
        return response

    def run_test(self, run_cmd, id, env={}):
        """Run test command and get the result as xml file if the running command is following junit otherwise result will be log.

        :param run_cmd: test command to be run.
        :type run_cmd: str
        :param id: DB's id of this run details.
        :type id: str
        :param env: environment variables needed in running tests.
        :type env: dict
        :return: path to xml file if exist and subprocess object containing (returncode, stdout, stderr)
        """
        response = self.execute_command(run_cmd, id=id, ip=self.container_name, environment=env)
        file_path = "/var/zeroci/{}.xml".format(self.random_string())
        remote_path = "/test.xml"
        copied = self.get_remote_file(ip=self.container_name, remote_path=remote_path, local_path=file_path)
        if copied:
            file_path = file_path
            delete_cmd = f"rm -f {remote_path}"
            self.execute_command(delete_cmd, id=id, ip=self.container_name)
        else:
            if os.path.exists(file_path):
                os.remove(file_path)
            file_path = None
        return response, file_path

    def prepare_script(self):
        return """export DEBIAN_FRONTEND=noninteractive &&
        apt-get update &&
        apt-get install -y git python3.6 python3-pip software-properties-common &&
        pip3 install black==19.10b0 &&
        """

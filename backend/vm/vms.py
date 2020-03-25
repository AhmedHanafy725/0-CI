import os
import random
import time
from urllib.parse import urlparse

import paramiko
import redis

from Jumpscale import j
from utils.utils import Utils

RETRIES = 10


class Complete_Executuion:
    returncode = None
    stdout = None

    def __init__(self, rc, out):
        self.returncode = rc
        self.stdout = out


class VMS(Utils):
    def __init__(self):
        super().__init__()
        self.node = None

    def list_nodes(self):
        """List farm nodes.

        :return: list of farm ips
        :return type: list
        """
        ips = []
        try:
            farm = j.sal_zos.farm.get("freefarm")
            nodes = farm.filter_online_nodes()
            for node in nodes:
                url = node["robot_address"]
                ip = urlparse(url).hostname
                ips.append(ip)
        except:
            ips = [
                "10.102.18.170",
                "110.102.52.108",
                "10.102.143.133",
            ]
        return ips

    def get_node(self):
        """Get node ip from farm randomly.

        :return: node ip
        :return type: str
        """
        # should pick with a rule
        nodes = self.list_nodes()
        node = random.choice(nodes)
        return node

    def load_ssh_key(self):
        """Load sshkey if it is exist or genertate one if not.

        :return: public key
        :return type: str
        """
        home_user = os.path.expanduser("~")
        if os.path.exists("{}/.ssh/id_rsa.pub".format(home_user)):
            with open("{}/.ssh/id_rsa.pub".format(home_user), "r") as file:
                ssh = file.readline().replace("\n", "")
        else:
            cmd = 'ssh-keygen -t rsa -N "" -f {}/.ssh/id_rsa -q -P ""; ssh-add {}/.ssh/id_rsa'.format(
                home_user, home_user
            )
            self.execute_cmd(cmd)
            ssh = self.load_ssh_key()
        return ssh

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

    def get_remote_file(self, ip, port, remote_path, local_path):
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
        if prequisties:
            if {"docker", "jsx"}.issubset(set(prequisties)):
                self.flist = "https://hub.grid.tf/qa_tft_1/jsx_docker.flist"
                self.disk_path = "/var/cache/{}.qcow2".format(self.random_string())
                self.node.client.bash("qemu-img create -f qcow2 {} 30G".format(self.disk_path)).get()
                self.media.append({"url": self.disk_path})

            elif "docker" in prequisties:
                self.flist = "https://hub.grid.tf/qa_tft_1/ubuntu18.04_docker.flist"
                self.disk_path = "/var/cache/{}.qcow2".format(self.random_string())
                self.node.client.bash("qemu-img create -f qcow2 {} 30G".format(self.disk_path)).get()
                self.media.append({"url": self.disk_path})

            elif "jsx" in prequisties:
                self.flist = "https://hub.grid.tf/qa_tft_1/jsx.flist"

    def deploy_vm(self, prequisties=""):
        """Deploy a virtual machine on zos node.

        :param prequisties: list of prequisties needed.
        :type prequisties: list
        :return: bool (True: if virtual machine is created).
        """
        iyo_name = self.random_string()
        iyo = j.clients.itsyouonline.get(
            iyo_name, baseurl="https://itsyou.online/api", application_id=self.iyo_id, secret=self.iyo_secret
        )
        self.jwt = iyo.jwt_get(scope="user:memberof:threefold.sysadmin").jwt
        self.ssh_key = self.load_ssh_key()
        self.cpu = 4
        self.memory = 4096
        self.media = []
        self.flist = "https://hub.grid.tf/qa_tft_1/ubuntu:18.04.flist"
        for _ in range(RETRIES):
            self.vm_name = self.random_string()
            self.node_ip = self.get_node()
            self.client_name = self.random_string()
            self.node = j.clients.zos.get(self.client_name, host=self.node_ip, password=self.jwt)
            self.port = random.randint(22000, 25000)
            self.ports = {self.port: 22}
            try:
                self.prepare(prequisties=prequisties)
                self.vm_uuid = self.node.client.container.create(
                    root_url=self.flist,
                    port=self.ports,
                    nics=[{"type": "default"}],
                    config={"/root/.ssh/authorized_keys": self.ssh_key},
                ).get()
                cl = self.node.client.container.client(self.vm_uuid)
                cl.bash("service ssh start").get()
                cl.filesystem.chmod("/etc/ssh", 0o700, True)
                break
            except:
                if self.media:
                    self.node.client.bash("rm -rf {}".format(self.disk_path)).get()
                time.sleep(1)
                self.vm_uuid = None

        time.sleep(40)
        if self.vm_uuid:
            return True
        return

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
        response = self.execute_command(cmd=script, id=id, ip=self.node_ip, port=self.port, environment=env)
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
        response = self.execute_command(run_cmd, id=id, ip=self.node_ip, port=self.port, environment=env)
        file_path = "/var/zeroci/{}.xml".format(self.random_string())
        remote_path = "/test.xml"
        copied = self.get_remote_file(ip=self.node_ip, port=self.port, remote_path=remote_path, local_path=file_path)
        if copied:
            file_path = file_path
            delete_cmd = f"rm -f {remote_path}"
            self.execute_command(delete_cmd, id=id, ip=self.node_ip, port=self.port)
        else:
            if os.path.exists(file_path):
                os.remove(file_path)
            file_path = None
        return response, file_path

    def destroy_vm(self):
        """Destory the virtual machine after finishing test.
        """
        if self.vm_uuid:
            self.node.client.container.terminate(int(self._vm_uuid))
        if self.media:
            self.node.client.bash("rm -rf {}".format(self.disk_path)).get()

    def prepare_script(self):
        return """export DEBIAN_FRONTEND=noninteractive &&
        apt-get update &&
        apt-get install -y git python3.6 python3-pip software-properties-common &&
        apt-get install -y --reinstall python3-apt &&
        pip3 install black==19.10b0 &&
        """

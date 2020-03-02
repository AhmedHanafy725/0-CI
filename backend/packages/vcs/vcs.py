from abc import ABCMeta, abstractmethod
import base64
import time
from utils.config import Configs
from github import Github as GH
import giteapy

c = Configs()


class VCSInterface(metaclass=ABCMeta):
    """The Version Control System Interface"""

    def get_content_in_text(function):
        def wrapper(*args, **kwargs):
            content_b64 = function(*args, **kwargs)
            if content_b64:
                content = base64.b64decode(content_b64.content)
                content = content.decode()
                return content
            return

        return wrapper

    def get_branches_names(function):
        def wrapper(*args, **kwargs):
            branches = function(*args, **kwargs)
            if branches == None:
                return
            branches_names = []
            for branch in branches:
                branches_names.append(branch.name)
            return branches_names

        return wrapper

    def call_trial(function):
        def wrapper(self, *args, **kwargs):
            for _ in range(5):
                try:
                    result = function(self, *args, **kwargs)
                    break
                except Exception:
                    time.sleep(1)
            else:
                return
            return result

        return wrapper

    @abstractmethod
    def status_send(status, link, commit):
        """An inteface method to send commit status

        :param status: should be one of [error, failure, pending, success].
        :type status: str
        :param link: the result file link to be accessed through the server.
        :type link: str
        :param commit: commit hash required to change its status on github.
        :type commit: str
        """

    @abstractmethod
    def get_content(ref, file_path):
        """An inteface method to get content

        :param ref: name of the commit/branch/tag.
        :type ref: str
        :param file_path: file path in the repo
        :type file_path: str
        """

    @abstractmethod
    def get_branches():
        """An inteface method to get branches"""


class Github(VCSInterface):
    """Github Class which implements VCSInterface"""

    def __init__(self, repo):
        """
        :param repo: full repo name
        :type repo: str
        """
        self.repo = repo
        self.github_cl = GH(c.vcs_token)
        self.repo_obj = self.github_cl.get_repo(self.repo)

    @VCSInterface.call_trial
    def status_send(
        self, status, link, commit, description="JSX-machine for testing", context="continuous-integration/zeroCI"
    ):

        commit_obj = self.repo_obj.get_commit(commit)
        commit_obj.create_status(state=status, target_url=link, description=description, context=context)

    @VCSInterface.get_content_in_text
    @VCSInterface.call_trial
    def get_content(self, ref, file_path):
        content_b64 = self.repo_obj.get_contents(file_path, ref=ref)
        return content_b64

    @VCSInterface.get_branches_names
    @VCSInterface.call_trial
    def get_branches(self):
        branches = self.repo_obj.get_branches()
        return branches


class Gitea(VCSInterface):
    """Gitea Class which implements VCSInterface"""

    def __init__(self, repo):
        """
        :param repo: full repo name
        :type repo: str
        """

        def _get_gitea_cl():
            configuration = giteapy.Configuration()
            configuration.host = c.vcs_host + "/api/v1"
            configuration.api_key["token"] = c.vcs_token
            return giteapy.api_client.ApiClient(configuration)

        self.repo = repo
        self.owner = repo.split("/")[0]  # org name
        self.repo_name = self.repo.split("/")[-1]
        self.repo_obj = giteapy.RepositoryApi(_get_gitea_cl())

    @VCSInterface.call_trial
    def status_send(
        self, status, link, commit, description="JSX-machine for testing", context="continuous-integration/zeroCI",
    ):
        body = {"context": context, "description": description, "state": status, "target_url": link}
        self.repo_obj.repo_create_status(self.owner, self.repo_name, commit, body=body)

    @VCSInterface.get_content_in_text
    @VCSInterface.call_trial
    def get_content(self, ref, file_path):
        content_b64 = self.repo_obj.repo_get_contents(self.owner, self.repo_name, file_path, ref=ref)
        return content_b64

    @VCSInterface.get_branches_names
    @VCSInterface.call_trial
    def get_branches(self):
        branches = self.repo_obj.repo_list_branches(self.owner, self.repo_name)
        return branches


class VCSFactory:
    """The Version Control System Factory Class"""

    @staticmethod
    def get_cvn(repo):
        if c.vcs_type == "github":
            return Github(repo)
        else:
            return Gitea(repo)

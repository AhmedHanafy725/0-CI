from abc import ABCMeta, abstractmethod
import base64
import time
from models.initial_config import InitialConfig
from github import Github as GH
import giteapy

configs = InitialConfig()


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

    @abstractmethod
    def get_last_commit(branch):
        """Get last commit's hash on a branch in a repository.

        :param repo: full repo name
        :type repo: str
        :param repo: branch name
        :type repo: str
        :return type: tuple
        """

    @abstractmethod
    def get_committer(commit):
        """Get the committer for commit's hash in a repository.

        :param repo: full repo name
        :type repo: str
        :param repo: branch name
        :type repo: str
        :return type: tuple
        """


class Github(VCSInterface):
    """Github Class which implements VCSInterface"""

    def __init__(self, repo):
        """
        :param repo: full repo name
        :type repo: str
        """
        if configs.configured:
            self.repo = repo
            self.github_cl = GH(configs.vcs_token)
            self.repo_obj = self.github_cl.get_repo(self.repo)

    @VCSInterface.call_trial
    def status_send(
        self, status, link, commit, description="ZeroCI for testing", context="continuous-integration/ZeroCI"
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

    @VCSInterface.call_trial
    def get_last_commit(self, branch):
        branch_obj = self.repo_obj.get_branch(branch)
        last_commit = branch_obj.commit.sha
        return last_commit

    @VCSInterface.call_trial
    def get_committer(self, commit):
        commit_obj = self.repo_obj.get_commit(commit)
        committer = commit_obj.author.login
        return committer


class Gitea(VCSInterface):
    """Gitea Class which implements VCSInterface"""

    def __init__(self, repo):
        """
        :param repo: full repo name
        :type repo: str
        """

        def _get_gitea_cl():
            configuration = giteapy.Configuration()
            configuration.host = configs.vcs_host + "/api/v1"
            configuration.api_key["token"] = configs.vcs_token
            return giteapy.api_client.ApiClient(configuration)

        if configs.configured:
            self.repo = repo
            self.owner = repo.split("/")[0]  # org name
            self.repo_name = self.repo.split("/")[-1]
            self.repo_obj = giteapy.RepositoryApi(_get_gitea_cl())

    @VCSInterface.call_trial
    def status_send(
        self, status, link, commit, description="ZeroCI for testing", context="continuous-integration/ZeroCI",
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

    @VCSInterface.call_trial
    def get_last_commit(self, branch):
        branch_obj = self.repo_obj.repo_get_branch(self.owner, self.repo_name, branch)
        last_commit = branch_obj.commit.id
        return last_commit

    @VCSInterface.call_trial
    def get_committer(self, commit):
        commit_obj = self.repo_obj.repo_get_single_commit(self.owner, self.repo_name, commit)
        committer = commit_obj.author.login
        return committer


class VCSFactory:
    """The Version Control System Factory Class"""

    @staticmethod
    def get_cvn(repo):
        if configs.vcs_type == "github":
            return Github(repo)
        else:
            return Gitea(repo)

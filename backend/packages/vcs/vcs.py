import base64
import time
from abc import ABCMeta, abstractmethod
from urllib.parse import urljoin

import giteapy
from github import Github as GH
from github import UnknownObjectException
from github.GithubException import GithubException
from models.initial_config import InitialConfig


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

    @abstractmethod
    def get_user_repos(username):
        """Get all user repositories.

        :param username: user name on vcs
        :type username: str
        :return type: list
        """

    @abstractmethod
    def get_org_repos(org_name):
        """Get all organization repositories.

        :param username: organization name on vcs
        :type username: str
        :return type: list
        """

    @abstractmethod
    def create_hook(repo):
        """Create web hook for zeroci.

        :param repo: repo full name
        :type repo: str
        """

    @abstractmethod
    def list_hooks(repo):
        """List web hooks in a repo.

        :param repo: repo full name
        :type repo: str
        """

    @abstractmethod
    def delete_hook(repo):
        """Delete web hook.

        :param repo: repo full name
        :type repo: str
        """


class Github(VCSInterface):
    """Github Class which implements VCSInterface"""

    def __init__(self, repo=None):
        """
        :param repo: full repo name
        :type repo: str
        """
        configs = InitialConfig()
        self.HOOK_URL = urljoin(configs.domain, "git_trigger")
        if configs.vcs_token:
            self.github_cl = GH(configs.vcs_token)
            if repo:
                self._set_repo_obj(repo)

    def _set_repo_obj(self, repo):
        self.repo = repo
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

    def _get_property_in_objs_list(self, objs, property=None):
        i = 0
        obj_list = objs.get_page(i)
        obj_results = []
        while obj_list:
            obj_list = objs.get_page(i)
            for obj in obj_list:
                if property:
                    obj_results.append(getattr(obj, property))
                else:
                    obj_results.append(obj)
            i += 1
        return obj_results

    def get_user_repos(self, username):
        user = self.github_cl.get_user(username)
        repos = user.get_repos()
        return self._get_property_in_objs_list(objs=repos, property="full_name")

    def get_org_repos(self, org_name):
        user = self.github_cl.get_organization(org_name)
        repos = user.get_repos()
        return self._get_property_in_objs_list(objs=repos, property="full_name")

    def create_hook(self, repo):
        repo = self.github_cl.get_repo(repo)
        hook_config = {"url": self.HOOK_URL, "content_type": "json"}
        try:
            repo.create_hook(name="web", config=hook_config, events=["push", "pull_request"], active=True)
        except (UnknownObjectException, GithubException) as e:
            if e.status in [404, 403]:
                return False
        return True

    def list_hooks(self, repo):
        repo = self.github_cl.get_repo(repo)
        hooks = repo.get_hooks()
        try:
            hooks = self._get_property_in_objs_list(objs=hooks)
        except (UnknownObjectException, GithubException) as e:
            if e.status in [404, 403]:
                return False
        return hooks

    def delete_hook(self, repo):
        hooks = self.list_hooks(repo=repo)
        if hooks == False:
            return False
        for hook in hooks:
            if hook.config["url"] == self.HOOK_URL:
                hook.delete()
        return True


class Gitea(VCSInterface):
    """Gitea Class which implements VCSInterface"""

    def __init__(self, repo=None):
        """
        :param repo: full repo name
        :type repo: str
        """
        configs = InitialConfig()
        self.HOOK_URL = urljoin(configs.domain, "git_trigger")

        def _get_gitea_cl():
            configuration = giteapy.Configuration()
            configuration.host = urljoin(configs.vcs_host, "/api/v1")
            configuration.api_key["token"] = configs.vcs_token
            return giteapy.api_client.ApiClient(configuration)

        if configs.vcs_token:
            self.repo_obj = giteapy.RepositoryApi(_get_gitea_cl())
            self.user_obj = giteapy.UserApi(_get_gitea_cl())
            self.org_obj = giteapy.OrganizationApi(_get_gitea_cl())

            if repo:
                self._set_repo_obj(repo)

    def _set_repo_obj(self, repo):
        self.repo = repo
        self.owner = repo.split("/")[0]  # org name
        self.repo_name = self.repo.split("/")[-1]

    @VCSInterface.call_trial
    def status_send(
        self,
        status,
        link,
        commit,
        description="ZeroCI for testing",
        context="continuous-integration/ZeroCI",
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

    def _get_rpeos_names(self, repos):
        repos_names = []
        for repo in repos:
            repos_names.append(repo.full_name)
        return repos_names

    def get_user_repos(self, username):
        repos = self.user_obj.user_list_repos(username)
        return self._get_rpeos_names(repos)

    def get_org_repos(self, org_name):
        repos = self.org_obj.org_list_repos(org_name)
        return self._get_rpeos_names(repos)

    def create_hook(self, repo):
        owner = repo.split("/")[0]  # org name
        repo_name = repo.split("/")[-1]
        hooks = self.list_hooks(repo=repo)
        for hook in hooks:
            if hook.config["url"] == self.HOOK_URL:
                return True

        config = giteapy.CreateHookOption(
            active=True,
            config={"url": self.HOOK_URL, "content_type": "json"},
            events=["push", "pull_request"],
            type="gitea",
        )
        try:
            self.repo_obj.repo_create_hook(owner, repo_name, body=config)
        except Exception as e:
            if e.status == 401:
                return False
        return True

    def list_hooks(self, repo):
        owner = repo.split("/")[0]  # org name
        repo_name = repo.split("/")[-1]
        try:
            hooks = self.repo_obj.repo_list_hooks(owner, repo_name)
        except Exception as e:
            if e.status == 401:
                return False
        return hooks

    def delete_hook(self, repo):
        hooks = self.list_hooks(repo=repo)
        if hooks == False:
            return False
        for hook in hooks:
            if hook.config["url"] == self.HOOK_URL:
                hook_id = hook.id

        owner = repo.split("/")[0]  # org name
        repo_name = repo.split("/")[-1]
        self.repo_obj.repo_delete_hook(owner, repo_name, hook_id)
        return True


class VCSFactory:
    """The Version Control System Factory Class"""

    @staticmethod
    def get_cvn(repo=None):
        configs = InitialConfig()
        if configs.vcs_type == "github":
            return Github(repo)
        else:
            return Gitea(repo)

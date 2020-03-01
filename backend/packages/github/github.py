import time
import base64
import yaml

from github import Github as GH

from utils.config import Configs
from bcdb.bcdb import RepoRun

RETRIES = 5


class Github(Configs):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.github_cl = GH(self.github_token)

    def status_send(
        self, status, link, repo, commit, description="JSX-machine for testing", context="continuous-integration/zeroCI"
    ):
        """Change github commit status.
        
        :param status: should be one of [error, failure, pending, success].
        :type status: str
        :param link: the result file link to be accessed through the server.
        :type link: str
        :param repo: full repo name
        :type repo: str
        :param commit: commit hash required to change its status on github.
        :type commit: str
        """
        for _ in range(RETRIES):
            try:
                repo_obj = self.github_cl.get_repo(repo)
                commit_obj = repo_obj.get_commit(commit)
                commit_obj.create_status(state=status, target_url=link, description=description, context=context)
                break
            except Exception:
                time.sleep(1)

    def get_content(self, repo, ref, file_path="0-Test.sh"):
        """Get file content from github with specific ref.

        :param repo: full repo name
        :type repo: str
        :param ref: name of the commit/branch/tag.
        :type ref: str
        :param file_path: file path in the repo
        :type file_path: str
        """
        for _ in range(RETRIES):
            try:
                repo = self.github_cl.get_repo(repo)
                content_b64 = repo.get_contents(file_path, ref=ref)
                break
            except Exception:
                time.sleep(1)
        else:
            return None
        content = base64.b64decode(content_b64.content)
        content = content.decode()
        return content

    def install_test_scripts(self, id):
        """Read 0-CI yaml script from the repo home directory and divide it to (prequisties, install, test) scripts.

        :param id: mongo record id to get commit information.
        :type id: str
        :return: prequisties, install, test script.
        """
        repo_run = RepoRun(id=id)
        org_repo_name = repo_run.repo.split("/")[0]
        clone = """mkdir -p /opt/code/github/{org_repo_name} &&
        cd /opt/code/github/{org_repo_name} &&
        git clone https://github.com/{repo}.git --branch {branch} &&
        cd /opt/code/github/{repo} &&
        git reset --hard {commit} &&
        """.format(
            repo=repo_run.repo, branch=repo_run.branch, commit=repo_run.commit, org_repo_name=org_repo_name
        ).replace(
            "\n", " "
        )

        script = self.get_content(repo=repo_run.repo, ref=repo_run.commit, file_path="zeroCI.yaml")
        if script:
            yaml_script = yaml.load(script)
            prequisties = yaml_script.get("prequisties")
            install = " && ".join(yaml_script.get("install"))
            install_script = clone + install
            test_script = yaml_script.get("script")
            return prequisties, install_script, test_script
        return None, None, None

    def get_branches(self, repo):
        """Get all branches names in a repository.

        :param repo: full repo name
        :type repo: str
        :return type: list
        """
        branches_names = []
        for _ in range(RETRIES):
            try:
                repo_obj = self.github_cl.get_repo(repo)
                branches = repo_obj.get_branches()
            except:
                time.sleep(0.1)

            for branch in branches:
                branches_names.append(branch.name)

            return branches_names

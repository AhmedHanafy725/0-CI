from Jumpscale import j

from .bcdb import Base


class TriggerRun(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.trigger
    timestamp** = (F)
    repo** = (S)
    branch** = (S)
    commit** = (S)
    committer** = (S)
    status** = (S)
    result = (dict)
    """
    _schema = j.data.schema.get_from_text(_schema_text)
    _model = _bcdb.model_get(schema=_schema)

    def __init__(self, **kwargs):
        if "id" in kwargs.keys():
            self._model_obj = self._model.find(id=kwargs["id"])[0]
        else:
            self._model_obj = self._model.new()
            self._model_obj.timestamp = kwargs["timestamp"]
            self._model_obj.repo = kwargs["repo"]
            self._model_obj.branch = kwargs["branch"]
            self._model_obj.commit = kwargs["commit"]
            self._model_obj.committer = kwargs["committer"]
            self._model_obj.status = kwargs.get("status", "pending")
            self._model_obj.result = {"result": []}
            self._model_obj.result["result"] = kwargs.get("result", [])

    @property
    def timestamp(self):
        return self._model_obj.timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        self._model_obj.timestamp = timestamp

    @property
    def status(self):
        return self._model_obj.status

    @status.setter
    def status(self, status):
        self._model_obj.status = status

    @property
    def result(self):
        return self._model_obj.result["result"]

    @result.setter
    def result(self, result):
        self._model_obj.result["result"] = result

    @property
    def repo(self):
        return self._model_obj.repo

    @repo.setter
    def repo(self, repo):
        self._model_obj.repo = repo

    @property
    def branch(self):
        return self._model_obj.branch

    @branch.setter
    def branch(self, branch):
        self._model_obj.branch = branch

    @property
    def commit(self):
        return self._model_obj.commit

    @commit.setter
    def commit(self, commit):
        self._model_obj.commit = commit

    @property
    def committer(self):
        return self._model_obj.committer

    @committer.setter
    def committer(self, committer):
        self._model_obj.committer = committer

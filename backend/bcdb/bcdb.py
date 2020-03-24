from Jumpscale import j


class Base:
    _model = None
    _model_obj = None

    def save(self):
        self._model_obj.save()

    @property
    def id(self):
        return self._model_obj.id

    @classmethod
    def distinct(cls, field, where=None):
        result = cls._model.query_model([f"distinct {field}"], whereclause=where).fetchall()
        distinct_list = []
        for i in result:
            for j in i:
                distinct_list.append(j)
        return distinct_list

    @classmethod
    def get_objects(cls, fields, where=None, order_by=None, asc=True):
        fields_string = ", ".join([f"[{x}]" for x in fields])
        query = f"select {fields_string}, [id] FROM {cls._model.index.sql_table_name}"
        if where:
            query += f" where {where}"
        if order_by:
            order = "asc" if asc else "desc"
            query += f" order by {order_by} {order}"
        query += ";"
        values = cls._model.query(query).fetchall()
        results = []
        for value in values:
            obj = {}
            for i, field in enumerate(fields):
                obj[field] = value[i]
            obj["id"] = value[i + 1]
            results.append(obj)
        return results


class RepoRun(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.repo
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


class ProjectRun(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.project
    timestamp** = (F)
    project_name** = (S)
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
            self._model_obj.project_name = kwargs["project_name"]
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
    def project_name(self):
        return self._model_obj.project_name

    @project_name.setter
    def project_name(self, project_name):
        self._model_obj.project_name = project_name


class RunConfig(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.run_config
    name** = (S)
    env = (dict)
    """
    _schema = j.data.schema.get_from_text(_schema_text)
    _model = _bcdb.model_get(schema=_schema)

    def __init__(self, **kwargs):
        if "id" in kwargs.keys():
            self._model_obj = self._model.find(id=kwargs["id"])[0]
        else:
            self._model_obj = self._model.new()
            self._model_obj.name = kwargs["name"]
            self._model_obj.status = kwargs.get("env", {})

    @property
    def name(self):
        return self._model_obj.name

    @name.setter
    def name(self, name):
        self._model_obj.name = name

    @property
    def env(self):
        return self._model_obj.env

    @env.setter
    def env(self, env):
        self._model_obj.env = env

    @classmethod
    def find(cls, **kwargs):
        return cls._model.find(**kwargs)


class InitialConfig(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.initial_config
    configured = False (B)
    admins = {"admins": []} (dict)
    users = {"users": []} (dict)
    iyo_id = (S)
    iyo_secret = (S)
    domain = (S)
    chat_id = (S)
    bot_token = (S)
    vcs_host = (S)
    vcs_token = (S)
    repos = {"repos": []} (dict)
    """
    _schema = j.data.schema.get_from_text(_schema_text)
    _model = _bcdb.model_get(schema=_schema)

    def __init__(self):
        self._model_objs = self._model.find()
        if self._model_objs:
            self._model_obj = self._model_objs[0]
        else:
            self._model_obj = self._model.new()

    @property
    def configured(self):
        return self._model_obj.configured

    @configured.setter
    def configured(self, configured):
        self._model_obj.configured = configured

    @property
    def admins(self):
        return self._model_obj.admins["admins"]

    @admins.setter
    def admins(self, admins):
        self._model_obj.admins["admins"] = admins

    @property
    def users(self):
        return self._model_obj.users["users"]

    @users.setter
    def users(self, users):
        self._model_obj.users["users"] = users

    @property
    def iyo_id(self):
        return self._model_obj.iyo_id

    @iyo_id.setter
    def iyo_id(self, iyo_id):
        self._model_obj.iyo_id = iyo_id

    @property
    def iyo_secret(self):
        return self._model_obj.iyo_secret

    @iyo_secret.setter
    def iyo_secret(self, iyo_secret):
        self._model_obj.iyo_secret = iyo_secret

    @property
    def domain(self):
        return self._model_obj.domain

    @domain.setter
    def domain(self, domain):
        self._model_obj.domain = domain

    @property
    def chat_id(self):
        return self._model_obj.chat_id

    @chat_id.setter
    def chat_id(self, chat_id):
        self._model_obj.chat_id = chat_id

    @property
    def bot_token(self):
        return self._model_obj.bot_token

    @bot_token.setter
    def bot_token(self, bot_token):
        self._model_obj.bot_token = bot_token

    @property
    def vcs_host(self):
        return self._model_obj.vcs_host

    @vcs_host.setter
    def vcs_host(self, vcs_host):
        self._model_obj.vcs_host = vcs_host

    @property
    def vcs_token(self):
        return self._model_obj.vcs_token

    @vcs_token.setter
    def vcs_token(self, vcs_token):
        self._model_obj.vcs_token = vcs_token

    @property
    def repos(self):
        return self._model_obj.repos["repos"]

    @repos.setter
    def repos(self, repos):
        self._model_obj.repos["repos"] = repos

    @property
    def vcs_type(self):
        return self._get_vcs_type(self.vcs_host)

    @staticmethod
    def _get_vcs_type(vcs_host):
        if "github" in vcs_host:
            vcs_type = "github"
        else:
            vcs_type = "gitea"
        return vcs_type

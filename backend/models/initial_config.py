from Jumpscale import j

from .bcdb import Base


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

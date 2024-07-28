from mongoengine import fields, Document

class InitialConfigModel(Document):
    name = fields.StringField(default="Initial_config")
    configured = fields.BooleanField()
    admins = fields.ListField(default=[])
    users = fields.ListField(default=[])
    repos = fields.ListField(default=[])
    domain = fields.StringField()
    chat_id = fields.StringField()
    bot_token = fields.StringField()
    vcs_host = fields.StringField()
    vcs_token = fields.StringField()

    
    @property
    def vcs_type(self):
        return self._get_vcs_type(self.vcs_host)

    def _get_vcs_type(self, vcs_host):
        if "github" in vcs_host:
            vcs_type = "github"
        else:
            vcs_type = "gitea"
        return vcs_type

    meta = {"collection": "initial_config"}

class InitialConfig():
    _model = InitialConfigModel

    def __new__(cls, **kwargs):
        name = "initial_config"
        objs = cls._model.objects(name="initial_config").first()
        if objs:
            return objs
        else:
            return cls._model(name=name, **kwargs)

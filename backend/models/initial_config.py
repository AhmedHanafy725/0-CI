from mongoengine import fields, Document
from .base import ModelFactory

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

class InitialConfig(ModelFactory):
    _model = InitialConfigModel

    def __new__(self, **kwargs):
        name = "Initial_config"
        objs = self._model.objects(name="Initial_config")
        if objs:
            return objs.first()
        else:
            return self._model(name=name, **kwargs)

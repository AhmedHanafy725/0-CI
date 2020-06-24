from .base import fields, ModelFactory, Document, StoredFactory


class InitialConfigModel(Document):
    configured = fields.Boolean()
    admins = fields.List(field=fields.String())
    users = fields.List(field=fields.String())
    repos = fields.List(field=fields.String())
    domain = fields.String()
    chat_id = fields.String()
    bot_token = fields.String()
    vcs_host = fields.String()
    vcs_token = fields.String()

    @property
    def vcs_type(self):
        return self._get_vcs_type(self.vcs_host)

    def _get_vcs_type(self, vcs_host):
        if "github" in vcs_host:
            vcs_type = "github"
        else:
            vcs_type = "gitea"
        return vcs_type


class InitialConfig(ModelFactory):
    _model = StoredFactory(InitialConfigModel)

    def __new__(self, **kwargs):
        name = "Intial_config"
        return self._model.get(name=name, **kwargs)

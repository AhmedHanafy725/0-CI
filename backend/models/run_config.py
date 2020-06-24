from .base import fields, ModelFactory, Document, StoredFactory


class RunConfigModel(Document):
    env = fields.Typed(dict, default={})


class RunConfig(ModelFactory):
    _model = StoredFactory(RunConfigModel)

    def __new__(self, **kwargs):
        kwargs["name"] = kwargs["name"].replace("/", "_")
        return self._model.get(**kwargs)

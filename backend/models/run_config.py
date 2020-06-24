from .base import fields, ModelFactory, Document, StoredFactory


class RunConfigModel(Document):
    env = fields.Typed(dict)


class RunConfig(ModelFactory):
    _model = StoredFactory(RunConfigModel)

    def __new__(self, **kwargs):
        return self._model.get(**kwargs)

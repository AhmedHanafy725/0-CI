from .base import Document, ModelFactory, fields, StoredFactory


class RunModel(Document):
    timestamp = fields.Integer(required=True, indexed=True)
    repo = fields.String(required=True)
    branch = fields.String(required=True)
    commit = fields.String(required=True)
    committer = fields.String(required=True)
    status = fields.String(required=True)
    bin_release = fields.String()
    triggered_by = fields.String(default="VCS Hook")
    result = fields.List(field=fields.Typed(dict))


class Run(ModelFactory):
    _model = StoredFactory(RunModel)

    def __new__(cls, **kwargs):
        name = "model" + str(int(kwargs["timestamp"] * 10 ** 6))
        kwargs["timestamp"] = int(kwargs["timestamp"])
        return cls._model.new(name=name, **kwargs)

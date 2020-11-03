from .base import fields, ModelFactory, Document, StoredFactory


class ScheduleInfoModel(Document):
    run_time = fields.String(required=True)
    branch = fields.String(required=True)
    created_by = fields.String(required=True)


class ScheduleInfo(ModelFactory):
    _model = StoredFactory(ScheduleInfoModel)

    def __new__(cls, **kwargs):
        name = kwargs["schedule_name"]
        return cls._model.new(name=name, **kwargs)

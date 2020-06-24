from .base import fields, ModelFactory, Document, StoredFactory


class ScheduleInfoModel(Document):
    prerequisites = fields.Typed(dict)
    install = fields.String(required=True)
    script = fields.List(field=fields.Typed(dict))
    run_time = fields.String(required=True)
    bin_path = fields.String()
    created_by = fields.String(required=True)

class ScheduleInfo(ModelFactory):
    _model = StoredFactory(ScheduleInfoModel)

    def __new__(self, **kwargs):
        name = kwargs["schedule_name"]
        return self._model.new(name=name, **kwargs)

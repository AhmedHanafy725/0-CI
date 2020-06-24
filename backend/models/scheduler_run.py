from .base import Document, ModelFactory, fields, StoredFactory


class ScheduleModel(Document):
    timestamp = fields.Integer(required=True, indexed=True)
    schedule_name = fields.String(required=True)
    status = fields.String(required=True)
    bin_release = fields.String()
    triggered_by = fields.String(default="ZeroCI Scheduler")
    result = fields.List(field=fields.Typed(dict))

class SchedulerRun(ModelFactory):
    _model = StoredFactory(ScheduleModel)

    def __new__(self, **kwargs):
        name = "model" + str(int(kwargs["timestamp"]* 10**6))
        kwargs["timestamp"] = int(kwargs["timestamp"])
        return self._model.new(name=name, **kwargs)

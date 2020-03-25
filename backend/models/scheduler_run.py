from Jumpscale import j

from .bcdb import Base


class SchedulerRun(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.schedule
    timestamp** = (F)
    schedule_name** = (S)
    status** = (S)
    result = (dict)
    """
    _schema = j.data.schema.get_from_text(_schema_text)
    _model = _bcdb.model_get(schema=_schema)

    def __init__(self, **kwargs):
        if "id" in kwargs.keys():
            self._model_obj = self._model.find(id=kwargs["id"])[0]
        else:
            self._model_obj = self._model.new()
            self._model_obj.timestamp = kwargs["timestamp"]
            self._model_obj.schedule_name = kwargs["schedule_name"]
            self._model_obj.status = kwargs.get("status", "pending")
            self._model_obj.result = {"result": []}
            self._model_obj.result["result"] = kwargs.get("result", [])

    @property
    def timestamp(self):
        return self._model_obj.timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        self._model_obj.timestamp = timestamp

    @property
    def status(self):
        return self._model_obj.status

    @status.setter
    def status(self, status):
        self._model_obj.status = status

    @property
    def result(self):
        return self._model_obj.result["result"]

    @result.setter
    def result(self, result):
        self._model_obj.result["result"] = result

    @property
    def schedule_name(self):
        return self._model_obj.schedule_name

    @schedule_name.setter
    def schedule_name(self, schedule_name):
        self._model_obj.schedule_name = schedule_name

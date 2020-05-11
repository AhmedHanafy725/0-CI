from Jumpscale import j

from .bcdb import Base


class ScheduleInfo(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.schedule.info
    name** = (S)
    install = (S)
    run_time = (S)
    script = (dict)
    prerequisites = (S)
    created_by = (S)
    """
    _schema = j.data.schema.get_from_text(_schema_text)
    _model = _bcdb.model_get(schema=_schema)

    def __init__(self, **kwargs):
        if list(kwargs.keys()) == ["name"]:
            self._model_obj = self._model.find(name=kwargs["name"])[0]
        else:
            self._model_obj = self._model.new()
            self._model_obj.name = kwargs["schedule_name"]
            self._model_obj.install_script = kwargs["install"]
            self._model_obj.run_time = kwargs["run_time"]
            self._model_obj.script = {"script": []}
            self._model_obj.script["script"] = kwargs.get("script", [])
            self._model_obj.prerequisites = kwargs["prerequisites"]
            self._model_obj.created_by = kwargs["created_by"]

    @property
    def name(self):
        return self._model_obj.name

    @name.setter
    def name(self, name):
        self._model_obj.name = name

    @property
    def install(self):
        return self._model_obj.install

    @install.setter
    def install(self, install):
        self._model_obj.install = install

    @property
    def run_time(self):
        return self._model_obj.run_time

    @run_time.setter
    def run_time(self, run_time):
        self._model_obj.run_time = run_time

    @property
    def script(self):
        return self._model_obj.script["script"]

    @script.setter
    def script(self, script):
        self._model_obj.script["script"] = script

    @property
    def prerequisites(self):
        return self._model_obj.prerequisites

    @prerequisites.setter
    def prerequisites(self, prerequisites):
        self._model_obj.prerequisites = prerequisites

    @property
    def created_by(self):
        return self._model_obj.created_by

    @created_by.setter
    def created_by(self, created_by):
        self._model_obj.created_by = created_by

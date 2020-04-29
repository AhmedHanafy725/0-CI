from Jumpscale import j

from .bcdb import Base


class ScheduleInfo(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.schedule.info
    name** = (S)
    install_script = (S)
    run_time = (S)
    test_script = (dict)
    prerequisites = (dict)
    """
    _schema = j.data.schema.get_from_text(_schema_text)
    _model = _bcdb.model_get(schema=_schema)

    def __init__(self, **kwargs):
        if list(kwargs.keys()) == ["name"]:
            self._model_obj = self._model.find(name=kwargs["name"])[0]
        else:
            self._model_obj = self._model.new()
            self._model_obj.name = kwargs["schedule_name"]
            self._model_obj.install_script = kwargs["install_script"]
            self._model_obj.run_time = kwargs["run_time"]
            self._model_obj.test_script = {"test_script": []}
            self._model_obj.test_script["test_script"] = kwargs.get("test_script", [])
            self._model_obj.prerequisites = {"prerequisites": []}
            self._model_obj.prerequisites["prerequisites"] = kwargs.get("prerequisites", [])

    @property
    def name(self):
        return self._model_obj.name

    @name.setter
    def name(self, name):
        self._model_obj.name = name

    @property
    def install_script(self):
        return self._model_obj.install_script

    @install_script.setter
    def install_script(self, install_script):
        self._model_obj.install_script = install_script

    @property
    def run_time(self):
        return self._model_obj.run_time

    @run_time.setter
    def run_time(self, run_time):
        self._model_obj.run_time = run_time

    @property
    def test_script(self):
        return self._model_obj.test_script["test_script"]

    @test_script.setter
    def test_script(self, test_script):
        self._model_obj.test_script["test_script"] = test_script

    @property
    def prerequisites(self):
        return self._model_obj.prerequisites["prerequisites"]

    @prerequisites.setter
    def prerequisites(self, prerequisites):
        self._model_obj.prerequisites["prerequisites"] = prerequisites

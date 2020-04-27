from Jumpscale import j

from .bcdb import Base


class RunConfig(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.run_config
    name** = (S)
    env = (dict)
    """
    _schema = j.data.schema.get_from_text(_schema_text)
    _model = _bcdb.model_get(schema=_schema)

    def __init__(self, **kwargs):
        if "id" in kwargs.keys():
            self._model_obj = self._model.find(id=kwargs["id"])[0]
        else:
            self._model_obj = self._model.new()
            self._model_obj.name = kwargs["name"]
            self._model_obj.status = kwargs.get("env", {})

    @property
    def name(self):
        return self._model_obj.name

    @name.setter
    def name(self, name):
        self._model_obj.name = name

    @property
    def env(self):
        return self._model_obj.env

    @env.setter
    def env(self, env):
        self._model_obj.env = env

    @classmethod
    def find(cls, **kwargs):
        return cls._model.find(**kwargs)

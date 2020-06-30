from mongoengine import fields, Document, connect


class RunConfig(Document):
    name = fields.StringField()
    env = fields.DictField(default={})

    meta = {"collection": "run_config", "indexes": ["name"]}

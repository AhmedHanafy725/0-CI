from mongoengine import fields, Document, connect


class TriggerModel(Document):
    timestamp = fields.FloatField(required=True, indexed=True)
    repo = fields.StringField(required=True)
    branch = fields.StringField(required=True)
    commit = fields.StringField(required=True)
    committer = fields.StringField(required=True)
    status = fields.StringField(required=True)
    bin_release = fields.StringField()
    triggered_by = fields.StringField(default="VCS Hook")
    result = fields.ListField()

    meta = {"collection": "schedule_info", "indexes": ["timestamp"]}


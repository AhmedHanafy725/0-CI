from mongoengine import fields, Document, connect


class ScheduleModel(Document):
    timestamp = fields.FloatField(required=True, indexed=True)
    schedule_name = fields.StringField(required=True)
    status = fields.StringField(required=True)
    bin_release = fields.StringField()
    triggered_by = fields.StringField(default="ZeroCI Scheduler")
    result = fields.ListField()

    meta = {"collection": "schedule_info", "indexes": ["timestamp"]}

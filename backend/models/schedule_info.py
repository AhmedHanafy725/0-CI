from mongoengine import fields, Document, connect


class ScheduleInfoModel(Document):
    name = fields.StringField()
    prerequisites = fields.DictField(dict)
    install = fields.StringField(required=True)
    script = fields.ListField(default=[])
    run_time = fields.StringField(required=True)
    bin_path = fields.StringField()
    created_by = fields.StringField(required=True)

    meta = {"collection": "schedule_info", "indexes": ["name"]}

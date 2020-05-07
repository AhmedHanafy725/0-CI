from datetime import datetime

def remove(type, days=30):
    bcdb = j.data.bcdb.get("zeroci")
    model = bcdb.model_get(f"zeroci.{type}")
    for obj in model.find():
        run_time = datetime.fromtimestamp(obj.timestamp)
        now_time = datetime.now()
        time_diff = now_time - run_time
        if time_diff.days > days:
            obj.delete()

def remove_schedule():
    bcdb = j.data.bcdb.get("zeroci")
    model = bcdb.model_get("zeroci.schedule")
    for obj in model.find():
        run_time = datetime.fromtimestamp(obj.timestamp)
        now_time = datetime.now()
        time_diff = now_time - run_time
        if time_diff.days > 30:
            obj.delete()
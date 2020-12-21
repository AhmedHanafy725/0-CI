import json

from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from actions.actions import Actions
from apis.base import app, check_configs, user
from bottle import HTTPResponse, abort, redirect, request
from models.schedule_info import ScheduleInfo
from models.scheduler_run import SchedulerRun

actions = Actions()
q = Queue(connection=Redis())
scheduler = Scheduler(connection=Redis())
PENDING = "pending"


@app.route("/api/schedule", method=["GET", "POST", "DELETE"])
@user
@check_configs
def schedule():
    if request.method == "GET":
        schedule_name = request.query.get("schedule_name")
        if schedule_name:
            schedule_info = ScheduleInfo.get_by_name(name=schedule_name)
            info = {
                "schedule_name": schedule_name,
                "install": schedule_info.install,
                "script": schedule_info.script,
                "prerequisites": schedule_info.prerequisites,
                "run_time": schedule_info.run_time,
                "created_by": schedule_info.created_by,
            }
            return json.dumps(info)

        schedules_names = ScheduleInfo.list_all()
        return json.dumps(schedules_names)

    if request.headers.get("Content-Type") == "application/json":
        if request.method == "POST":
            data = ["schedule_name", "run_time", "prerequisites", "install", "script", "bin_path"]
            job = {}
            for item in data:
                value = request.json.get(item)
                if not value:
                    if item == "bin_path":
                        continue
                    return HTTPResponse(f"{item} should have a value", 400)
                elif item is "script" and not isinstance(value, list):
                    return HTTPResponse(f"{item} should be str or list", 400)
                else:
                    job[item] = value

            created_by = request.environ.get("beaker.session").get("username").strip(".3bot")
            job["created_by"] = created_by

            if job["schedule_name"] in ScheduleInfo.list_all():
                return HTTPResponse(f"Schedule name {job['schedule_name']} is already used", 400)

            schedule_info = ScheduleInfo(**job)
            schedule_info.save()
            try:
                scheduler.cron(
                    cron_string=job["run_time"],
                    func=actions.schedule_run,
                    args=[job,],
                    run_id=job["schedule_name"],
                    timeout=-1,
                )
            except:
                return HTTPResponse("Wrong time format should be like (0 * * * *)", 400)
            return HTTPResponse("Added", 201)
        else:
            schedule_name = request.json.get("schedule_name")
            schedule_info = ScheduleInfo.get_by_name(name=schedule_name)
            schedule_info.delete()
            scheduler.cancel(schedule_name)
            return HTTPResponse("Removed", 200)
    return abort(400)


@app.route("/api/schedule_trigger", method=["POST", "GET"])
@user
@check_configs
def schedule_trigger():
    if request.method == "GET":
        redirect("/")

    if request.headers.get("Content-Type") == "application/json":
        schedule_name = request.json.get("schedule_name")

        where = {"schedule_name": schedule_name}
        runs = SchedulerRun.get_objects(fields=["status"], order_by="timestamp", asc=False, **where)
        if runs and runs[0]["status"] == PENDING:
            return HTTPResponse(
                f"There is a running job from this schedule {schedule_name}, please try again after this run finishes",
                503,
            )
        if schedule_name not in ScheduleInfo.list_all():
            return HTTPResponse(f"Schedule name {schedule_name} is not found", 400)

        schedule_info = ScheduleInfo.get_by_name(name=schedule_name)
        job = {
            "schedule_name": schedule_name,
            "prerequisites": schedule_info.prerequisites,
            "install": schedule_info.install,
            "script": schedule_info.script,
            "triggered_by": request.environ.get("beaker.session").get("username").strip(".3bot"),
            "bin_path": schedule_info.bin_path,
        }
        job = q.enqueue_call(func=actions.schedule_run, args=(job,), result_ttl=5000, timeout=20000,)
        if job:
            return HTTPResponse(job.get_id(), 200)
    return HTTPResponse("Wrong data", 400)

import json

from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from actions.actions import Actions
from apis.base import app, check_configs, user
from bottle import Response, abort, redirect, request
from models.schedule_info import ScheduleInfo
from models.scheduler_run import SchedulerRun

actions = Actions()
q = Queue(connection=Redis())
scheduler = Scheduler(connection=Redis())


@app.route("/api/schedule", method=["GET", "POST", "DELETE"])
@user
@check_configs
def schedule():
    if request.method == "GET":
        schedule_name = request.query.get("schedule_name")
        if schedule_name:
            schedule_info = ScheduleInfo(name=schedule_name)
            info = {
                "schedule_name": schedule_name,
                "install_script": schedule_info.install_script,
                "test_script": schedule_info.test_script,
                "prequisties": schedule_info.prequisties,
                "run_time": schedule_info.run_time,
            }
            return json.dumps(info)

        schedules_names = ScheduleInfo.distinct("name")
        return json.dumps(schedules_names)

    if request.headers.get("Content-Type") == "application/json":
        if request.method == "POST":
            data = ["schedule_name", "run_time"]
            list_str_data = ["install_script", "test_script", "prequisties"]
            data.extend(list_str_data)
            job = {}
            for item in data:
                value = request.json.get(item)
                if not value:
                    return Response(f"{item} should have a value", 400)
                elif item in list_str_data and not isinstance(value, (str, list)):
                    return Response(f"{item} should be str or list", 400)
                elif item not in list_str_data and not isinstance(value, str):
                    return Response(f"{item} should be str", 400)
                else:
                    job[item] = value

            if isinstance(job["install_script"], list):
                job["install_script"] = " && ".join(job["install_script"])

            if isinstance(job["test_script"], str):
                job["test_script"] = [job["test_script"]]

            if job["schedule_name"] in ScheduleInfo.distinct("name"):
                return Response("Schedule name {job['schedule_name']} is already used", 400)

            schedule_info = ScheduleInfo(**job)
            schedule_info.save()
            try:
                scheduler.cron(
                    cron_string=job["run_time"],
                    func=actions.schedule_run,
                    args=[job["schedule_name"], job["install_script"], job["test_script"], job["prequisties"],],
                    id=job["schedule_name"],
                    timeout=7200,
                )
            except:
                return Response("Wrong time format should be like (0 * * * *)", 400)
            return Response("Added", 201)
        else:
            schedule_name = request.json.get("schedule_name")
            schedule_info = ScheduleInfo(name=schedule_name)
            schedule_info.delete()
            scheduler.cancel(schedule_name)
            return Response("Removed", 200)
    return abort(400)


@app.route("/api/schedule_trigger", method=["POST", "GET"])
@user
@check_configs
def schedule_trigger():
    if request.method == "GET":
        redirect("/")

    if request.headers.get("Content-Type") == "application/json":
        schedule_name = request.json.get("schedule_name")

        where = f'schedule_name="{schedule_name}"'
        runs = SchedulerRun.get_objects(fields=["status"], where=where, order_by="timestamp", asc=False)
        if runs and runs[0]["status"] == "pending":
            return Response(
                f"There is a running job from this schedule {schedule_name}, please try again after this run finishes",
                503,
            )
        if schedule_name not in ScheduleInfo.distinct("name"):
            return Response(f"Schedule name {schedule_name} is not found", 400)

        schedule_info = ScheduleInfo(name=schedule_name)
        job = q.enqueue_call(
            func=actions.schedule_run,
            args=(schedule_name, schedule_info.install_script, schedule_info.test_script, schedule_info.prequisties,),
            result_ttl=5000,
            timeout=20000,
        )
        if job:
            return Response(job.get_id(), 200)
    return Response("Wrong data", 400)

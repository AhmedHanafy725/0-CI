from gevent import sleep
from redis import Redis
import json

from apis.base import app
from bottle import abort, request
from geventwebsocket import WebSocketError

redis = Redis()


@app.route("/websocket/logs/<id>")
def logs(id):
    wsock = request.environ.get("wsgi.websocket")
    if not wsock:
        abort(400, "Expected WebSocket request.")

    start = 0
    while start != -1:
        length = redis.llen(id)
        if start > length:
            break
        if start == length:
            sleep(0.01)
            continue
        result_list = redis.lrange(id, start, length)
        if b"hamada ok" in result_list:
            result_list.remove(b"hamada ok")
            start = -1
        else:
            start += len(result_list)
        results = ""
        for result in result_list:
            results += result.decode()
        if results:
            try:
                wsock.send(results)
            except WebSocketError:
                break


@app.route("/websocket/neph_logs/<neph_id>")
def neph_logs(neph_id):
    wsock = request.environ.get("wsgi.websocket")
    if not wsock:
        abort(400, "Expected WebSocket request.")

    start = 0
    while start != -1:
        length = redis.llen(neph_id)
        if start > length:
            break
        if start == length:
            sleep(0.01)
            continue

        result_list = redis.lrange(neph_id, start, length)
        start += len(result_list)
        results = ""
        for result in result_list:
            data = json.loads(result.decode())
            results += data["content"]
        if results:
            try:
                wsock.send(results)
            except WebSocketError:
                break


@app.route("/websocket/neph_jobs/<id>")
def neph_jobs(id):
    wsock = request.environ.get("wsgi.websocket")
    if not wsock:
        abort(400, "Expected WebSocket request.")

    start = {}
    while True:
        jobs = []
        for key in redis.keys():
            key = key.decode()
            if id in key and not key.startswith("neph") and key != id:
                if key not in start.keys():
                    start[key] = 0
                length = redis.llen(key)
                result_list = redis.lrange(key, start[key], length)
                start[key] += len(result)
                for result in result_list:
                    job_name = result.decode()
                    full_job_name = f"neph:{key}:{job_name}"
                    jobs.append(full_job_name)

        if not jobs:
            sleep(1)
            continue

        if jobs:
            try:
                wsock.send(json.dumps(jobs))
            except WebSocketError:
                break


@app.route("/websocket/status")
def update_status():
    wsock = request.environ.get("wsgi.websocket")
    if not wsock:
        abort(400, "Expected WebSocket request.")

    sub = redis.pubsub()
    sub.subscribe("zeroci_status")
    for msg in sub.listen():
        data = msg["data"]
        if isinstance(data, bytes):
            try:
                wsock.send(data.decode())
            except WebSocketError:
                break

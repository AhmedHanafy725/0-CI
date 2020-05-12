from gevent import sleep
from redis import Redis

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
            sleep(0.1)
        result_list = redis.lrange(id, start, length)
        if b"hamada ok" in result_list:
            result_list.remove(b"hamada ok")
            start = -1
        else:
            start += len(result_list)
        for result in result_list:
            try:
                wsock.send(result.decode())
            except WebSocketError:
                break


@app.route("/websocket/status")
def update_repos_table(repo, branch):
    wsock = request.environ.get("wsgi.websocket")
    if not wsock:
        abort(400, "Expected WebSocket request.")

    sub = redis.pubsub()
    sub.subscribe("zeroci_status")
    for msg in sub.listen():
        data = msg["data"]
        if isinstance(data, bytes):
            try:
                wsock.send(msg["data"].decode())
            except WebSocketError:
                break

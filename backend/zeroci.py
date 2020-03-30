from gevent.pywsgi import WSGIServer

from apis.base import *
from apis.config import *
from apis.login import *
from apis.results import *
from apis.schedule import *
from apis.trigger import *
from apis.websockets import *
from apis.default import *
from beaker.middleware import SessionMiddleware
from geventwebsocket.handler import WebSocketHandler


session_opts = {"session.type": "file", "session.data_dir": "./data", "session.auto": True}
app_with_session = SessionMiddleware(app, session_opts)
if __name__ == "__main__":
    server = WSGIServer(("0.0.0.0", 6010), app_with_session, handler_class=WebSocketHandler)
    server.serve_forever()

from gevent import monkey

monkey.patch_all(subprocess=False)

from gevent.pywsgi import WSGIServer

from apis.base import app
import apis.config
import apis.login
import apis.results
# import apis.schedule
import apis.trigger
import apis.websockets
import apis.default
from beaker.middleware import SessionMiddleware
from geventwebsocket.handler import WebSocketHandler

session_opts = {"session.type": "file", "session.data_dir": "./data", "session.auto": True}
app_with_session = SessionMiddleware(app, session_opts)
if __name__ == "__main__":
    server = WSGIServer(("0.0.0.0", 6010), app_with_session, handler_class=WebSocketHandler)
    server.serve_forever()

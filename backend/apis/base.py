from bottle import Bottle, Response, abort, redirect, request, response
from models.initial_config import InitialConfig
from functools import wraps

app = Bottle()
configs = InitialConfig()

LOGIN_URL = "/auth/login"


def login_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        session = request.environ.get("beaker.session")
        if not session.get("authorized", False):
            session["next_url"] = request.url
            return redirect(LOGIN_URL)
        return func(*args, **kwargs)

    return decorator


def check_configs(func):
    def wrapper(*args, **kwargs):
        if not configs.configured:
            return redirect("/initial_config")
        return func(*args, **kwargs)

    return wrapper


def user(func):
    @login_required
    def wrapper(*args, **kwargs):
        username = request.environ.get("beaker.session").get("username")
        if not (username in configs.users or (configs.admins and (username in configs.admins))):
            return abort(401)
        return func(*args, **kwargs)

    return wrapper


def admin(func):
    @login_required
    def wrapper(*args, **kwargs):
        username = request.environ.get("beaker.session").get("username")
        if configs.admins and (not username in configs.admins):
            return abort(401)
        return func(*args, **kwargs)

    return wrapper


@app.hook("after_request")
def enable_cors_disable_cache():
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "PUT, GET, POST, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

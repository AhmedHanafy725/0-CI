from bottle import Bottle, Response, abort, redirect, request, response
from Jumpscale import j
from models.initial_config import InitialConfig

app = Bottle()
configs = InitialConfig()
client = j.clients.oauth_proxy.get("zeroci")
oauth_app = j.tools.oauth_proxy.get(app, client, "/auth/login")
bot_app = j.tools.threebotlogin_proxy.get(app, "/auth/login")
PROVIDERS = list(client.providers_list())


def check_configs(func):
    def wrapper(*args, **kwargs):
        if not configs.configured:
            return redirect("/initial_config")
        return func(*args, **kwargs)

    return wrapper


def user(func):
    @oauth_app.login_required
    def wrapper(*args, **kwargs):
        username = request.environ.get("beaker.session").get("username")
        if not (username in configs.users or (configs.admins and (username in configs.admins))):
            return abort(401)
        return func(*args, **kwargs)

    return wrapper


def admin(func):
    @oauth_app.login_required
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

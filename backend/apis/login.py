import json

from apis.base import PROVIDERS, app, bot_app, oauth_app
from bottle import abort, redirect, request
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader("../dist"), autoescape=select_autoescape(["html", "xml"]))


@app.route("/auth/login")
def login():
    provider = request.query.get("provider")

    if provider:
        if provider == "3bot":
            next_url = request.query.get("next_url")
            if next_url:
                bot_app.session["next_url"] = next_url
            return bot_app.login(request.headers["HOST"], "/auth/3bot_callback")

        redirect_url = f"https://{request.headers['HOST']}/auth/oauth_callback"
        return oauth_app.login(provider, redirect_url=redirect_url)

    return env.get_template("login.html").render(providers=PROVIDERS)


@app.route("/auth/3bot_callback")
def threebot_callback():
    bot_app.callback()


@app.route("/auth/oauth_callback")
def oauth_callback():
    user_info = oauth_app.callback()
    oauth_app.session["email"] = user_info["email"]
    return redirect(oauth_app.next_url)


@app.route("/auth/logout")
def logout():
    session = request.environ.get("beaker.session", {})
    try:
        session.invalidate()
    except AttributeError:
        pass

    redirect(request.query.get("next_url", "/"))


@app.route("/auth/authenticated")
def is_authenticated():
    session = request.environ.get("beaker.session", {})
    if session.get("authorized"):
        username = session["username"]
        email = session["email"]
        return json.dumps({"username": username, "email": email})
    return abort(403)

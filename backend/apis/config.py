import json
import sys

import requests
from telegram import Bot
from telegram.error import BadRequest, InvalidToken, Unauthorized

from apis.base import admin, app, check_configs, configs, user
from bottle import HTTPResponse, abort, request
from models.run_config import RunConfig
from packages.vcs.vcs import VCSFactory


@app.route("/api/telegram_config", method=["GET", "POST"])
@admin
def validate_telegam():
    """Validate telegram token and chat ID
    """
    confs = ["chat_id", "bot_token"]
    conf_dict = {}
    if request.method == "GET":
        for conf in confs:
            conf_dict[conf] = getattr(configs, conf)
            conf_json = json.dumps(conf_dict)
        return conf_json
    if request.headers.get("Content-Type") == "application/json":
        for conf in confs:
            value = request.json.get(conf)
            if not value:
                return HTTPResponse(f"{conf} should have a value", 400)
            elif not isinstance(value, str):
                return HTTPResponse(f"{conf} should be str", 400)
            else:
                setattr(configs, conf, value)

        # Check telegram bot token
        try:
            bot = Bot(request.json["bot_token"])
            bot.sendMessage(request.json["chat_id"], "Configured")
        except (InvalidToken, BadRequest, Unauthorized) as error:
            if error.message == "Unauthorized":
                error.message += ": Invalid Token"
            return HTTPResponse(error.message, 400)

        configs.save()
        return HTTPResponse("Configured", 200)


@app.route("/api/vcs_config", method=["GET", "POST"])
@admin
def vcs_config():
    """Initial configuration for the ci before start working.
    """
    confs = ["domain", "vcs_host", "vcs_token"]
    conf_dict = {}
    if request.method == "GET":
        for conf in confs:
            conf_dict[conf] = getattr(configs, conf)
            conf_json = json.dumps(conf_dict)
        return conf_json
    if request.headers.get("Content-Type") == "application/json":
        for conf in confs:
            value = request.json.get(conf)
            if not value:
                return HTTPResponse(f"{conf} should have a value", 400)
            elif not isinstance(value, str):
                return HTTPResponse(f"{conf} should be str", 400)
            else:
                setattr(configs, conf, value)

        # Check vcs host is reachable
        try:
            requests.get(request.json["vcs_host"])
        except Exception:
            return HTTPResponse(f"Your version control system is not reachable", 400)

        configs.save()
        return HTTPResponse("Configured", 200)


@app.route("/api/repos_config", method=["GET", "POST"])
@admin
def repos_config():
    vcs_obj = VCSFactory().get_cvn()
    if request.method == "GET":
        username = request.query.get("username")
        org_name = request.query.get("org_name")
        if username:
            try:
                repos = vcs_obj.get_user_repos(username)
            except:
                return HTTPResponse("The token provided is invalid", 400)
        elif org_name:
            try:
                repos = vcs_obj.get_org_repos(org_name)
            except:
                return HTTPResponse("The token provided is invalid", 400)
        else:
            repos = configs.repos
        return json.dumps(repos)
    if request.headers.get("Content-Type") == "application/json":
        repos = request.json.get("repos")
        if not repos:
            return HTTPResponse(f"repos should have a value", 400)
        elif not isinstance(repos, list):
            return HTTPResponse("repos should be list", 400)
        else:
            added_repos = set(repos) - set(configs.repos)
            for repo in added_repos:
                created = vcs_obj.create_hook(repo)
                if not created:
                    return HTTPResponse(f"Make sure your token has full access for hooks on this repo {repo} and this repo is not archived", 401)

            removed_repos = set(configs.repos) - set(repos)
            for repo in removed_repos:
                deleted = vcs_obj.delete_hook(repo)
                if not deleted:
                    return HTTPResponse(f"Couldn't delete the hook of this repo {repo}", 401)

            configs.repos = repos
            configs.save()
            return HTTPResponse("Added", 201)


@app.route("/api/users", method=["GET", "POST", "DELETE"])
@admin
def users():
    if request.method == "GET":
        all_users = {"admins": configs.admins, "users": configs.users}
        all_json = json.dumps(all_users)
        return all_json
    if not request.headers.get("Content-Type") == "application/json":
        return abort(400)

    user = request.json.get("user")
    admin = request.json.get("admin")
    if request.method == "POST":
        if user:
            configs.users.append(user)
            configs.save()
            return HTTPResponse("Added", 200)
        if admin:
            configs.admins.append(admin)
            configs.save()
            return HTTPResponse("Added", 200)
    if request.method == "DELETE":
        if user and user in configs.users:
            configs.users.remove(user)
            configs.save()
            return HTTPResponse("Deleted", 200)
        if admin and admin in configs.admins:
            configs.admins.remove(admin)
            configs.save()
            return HTTPResponse("Deleted", 200)
    return abort(400)


@app.route("/api/apply_config", method=["POST"])
@admin
def apply_config():
    if not (configs.domain or configs.vcs_host or configs.vcs_token):
        return HTTPResponse("Version Control System is not configured")
    elif not (configs.bot_token or configs.chat_id):
        return HTTPResponse("Telegram is not configured")
    elif not configs.repos:
        return HTTPResponse("There is no repository at least you should have one")
    else:
        if not configs.admins:
            admin = request.environ.get("beaker.session").get("username")
            configs.admins.append(admin)
        configs.configured = True
        return HTTPResponse("Configured", 200)


@app.route("/api/run_config/<name:path>", method=["GET", "POST", "DELETE"])
@user
@check_configs
def run_config(name):
    run_config = RunConfig(name=name)
    if request.method == "POST":
        key = request.json["key"]
        value = request.json["value"]
        run_config.env[key] = value
        run_config.save()
        return HTTPResponse("Added", 201)
    elif request.method == "DELETE":
        key = request.json["key"]
        run_config.env.pop(key)
        run_config.save()
        return HTTPResponse("Deleted", 201)
    else:
        env = json.dumps(run_config.env)
        return env
    return abort(404)

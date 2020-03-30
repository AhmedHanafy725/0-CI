import json
import sys

from apis.base import admin, app, check_configs, configs, user
from bottle import Response, abort, request
from models.run_config import RunConfig


@app.route("/api/initial_config", method=["GET", "POST"])
@admin
def initial_config():
    """Initial configuration for the ci before start working.
    """
    confs = ["iyo_id", "iyo_secret", "domain", "chat_id", "bot_token", "vcs_host", "vcs_token", "repos"]
    conf_dict = {}
    if request.method == "GET":
        confs.extend(["configured", "admins", "users"])
        for conf in confs:
            conf_dict[conf] = getattr(configs, conf)
            conf_json = json.dumps(conf_dict)
        return conf_json
    if request.headers.get("Content-Type") == "application/json":
        for conf in confs:
            value = request.json.get(conf)
            if not value:
                return Response(f"{conf} should have a value", 400)
            elif conf is "repos" and not isinstance(value, list):
                return Response("repos should be str or list", 400)
            elif conf is not "repos" and not isinstance(value, str):
                return Response(f"{conf} should be str", 400)
            else:
                setattr(configs, conf, value)

        if not configs.admins:
            admin = request.environ.get("beaker.session").get("username")
            configs.admins.append(admin)
        configs.configured = True
        configs.save()
        sys.exit(1)


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
            return Response("Added", 200)
        if admin:
            configs.admins.append(admin)
            configs.save()
            return Response("Added", 200)
    if request.method == "DELETE":
        if user and user in configs.users:
            configs.users.remove(user)
            configs.save()
            return Response("Deleted", 200)
        if admin and admin in configs.admins:
            configs.admins.remove(admin)
            configs.save()
            return Response("Deleted", 200)
    return abort(400)


@app.route("/api/run_config/<name:path>", method=["GET", "POST", "DELETE"])
@user
@check_configs
def run_config(name):
    run_config = RunConfig.find(name=name)
    if run_config and len(run_config) == 1:
        run_config = run_config[0]
    else:
        run_config = RunConfig(name=name)
    if request.method == "POST":
        key = request.json["key"]
        value = request.json["value"]
        run_config.env[key] = value
        run_config.save()
        return Response("Added", 201)
    elif request.method == "DELETE":
        key = request.json["key"]
        run_config.env.pop(key)
        run_config.save()
        return Response("Deleted", 201)
    else:
        env = json.dumps(run_config.env)
        return env
    return abort(404)

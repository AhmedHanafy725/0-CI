from apis.base import app, check_configs
from bottle import static_file


@app.route("/static/<filepath:path>")
def static(filepath):
    return static_file(filepath, root="../dist/static")


@app.route("/bin/<filepath:path>")
def send_bin(filepath):
    return static_file(filepath, root="/sandbox/var/bin", download=filepath)


@app.route("/")
@app.route("/<path:path>")
@check_configs
def catch_all(path=""):
    return static_file("index.html", root="../dist")

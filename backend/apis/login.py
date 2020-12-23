import base64
import json
from urllib.parse import urlencode

import nacl
import requests
from bottle import abort, redirect, request
from models.initial_config import InitialConfig
from nacl.public import Box
from nacl.signing import VerifyKey
from utils.utils import Utils

from apis.base import app

CALLBACK_URL = "/auth/3bot_callback"
REDIRECT_URL = "https://login.threefold.me"


utils = Utils()
PRIV_KEY = nacl.signing.SigningKey.generate()


@app.route("/auth/login")
def login():
    provider = request.query.get("provider")
    session = request.environ.get("beaker.session")
    next_url = request.query.get("next_url", "/")

    public_key = PRIV_KEY.verify_key
    if provider and provider == "3bot":
        state = utils.random_string()
        session["next_url"] = next_url
        session["state"] = state
        app_id = request.get_header("host")
        params = {
            "state": state,
            "appid": app_id,
            "scope": json.dumps({"user": True, "email": True}),
            "redirecturl": CALLBACK_URL,
            "publickey": public_key.to_curve25519_public_key().encode(encoder=nacl.encoding.Base64Encoder).decode(),
        }
        params = urlencode(params)
        return redirect(f"{REDIRECT_URL}?{params}", code=302)


@app.route("/auth/3bot_callback")
def threebot_callback():
    session = request.environ.get("beaker.session")
    data = request.query.get("signedAttempt")

    if not data:
        return abort(400, "signedAttempt parameter is missing")

    data = json.loads(data)

    if "signedAttempt" not in data:
        return abort(400, "signedAttempt value is missing")

    username = data["doubleName"]

    if not username:
        return abort(400, "DoubleName is missing")

    res = requests.get(f"https://login.threefold.me/api/users/{username}", {"Content-Type": "application/json"})
    if res.status_code != 200:
        return abort(400, "Error getting user pub key")
    pub_key = res.json()["publicKey"]

    user_pub_key = VerifyKey(base64.b64decode(pub_key))

    # verify data
    signedData = data["signedAttempt"]

    verifiedData = user_pub_key.verify(base64.b64decode(signedData)).decode()

    data = json.loads(verifiedData)

    if "doubleName" not in data:
        return abort(400, "Decrypted data does not contain (doubleName)")

    if "signedState" not in data:
        return abort(400, "Decrypted data does not contain (state)")

    if data["doubleName"] != username:
        return abort(400, "username mismatch!")

    # verify state
    state = data["signedState"]
    if state != session["state"]:
        return abort(400, "Invalid state. not matching one in user session")

    nonce = base64.b64decode(data["data"]["nonce"])
    ciphertext = base64.b64decode(data["data"]["ciphertext"])

    try:
        box = Box(PRIV_KEY.to_curve25519_private_key(), user_pub_key.to_curve25519_public_key())
        decrypted = box.decrypt(ciphertext, nonce)
    except nacl.exceptions.CryptoError:
        return abort(400, "Error decrypting data")

    try:
        result = json.loads(decrypted)
    except json.JSONDecodeError:
        return abort(400, "3bot login returned faulty data")

    if "email" not in result:
        return abort(400, "Email is not present in data")

    email = result["email"]["email"]

    sei = result["email"]["sei"]
    res = requests.post(
        "https://openkyc.live/verification/verify-sei",
        headers={"Content-Type": "application/json"},
        json={"signedEmailIdentifier": sei},
    )

    if res.status_code != 200:
        return abort(400, "Email is not verified")

    session["username"] = username
    session["email"] = email
    session["authorized"] = True
    session["signedAttempt"] = signedData
    return redirect(session.get("next_url", "/"))


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
        configs = InitialConfig()
        username = session["username"]
        email = session["email"]
        if username in configs.admins:
            permission = "admin"
        elif username in configs.users:
            permission = "user"
        else:
            permission = ""
        return json.dumps({"username": username, "email": email, "permission": permission})
    return abort(403)

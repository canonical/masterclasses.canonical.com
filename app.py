# This file serves as an entry point for the rock image. It is required by the PaaS app charmer.
# The flask application must be defined in this file under the variable name `app`.
# See - https://documentation.ubuntu.com/rockcraft/en/latest/reference/extensions/flask-framework/

# The actual application lives in webapp/app.py; this re-exports it so that
# the extension can discover the standard `app:app` entrypoint.
import os

# Bridge paas-charm injected env names to the names this app expects.
# paas-charm Flask injects user config as FLASK_<KEY> and the postgresql
# relation as POSTGRESQL_DB_CONNECT_STRING; the app reads unqualified names.

if not os.environ.get("DATABASE_URL") and os.environ.get("POSTGRESQL_DB_CONNECT_STRING"):
    os.environ["DATABASE_URL"] = os.environ["POSTGRESQL_DB_CONNECT_STRING"]

for _var in (
    "ADMIN_EMAILS",
    "API_TOKEN",
    "BASE_URL",
    "CLIENT_EMAIL",
    "CLIENT_ID",
    "CLIENT_X509_CERT_URL",
    "DIRECTORY_API_TOKEN",
    "GMAIL_DELEGATE_ACCOUNT",
    "GOOGLE_PROJECT_ID",
    "MATTERMOST_DEV_WEBHOOK_URL",
    "OPENID_LAUNCHPAD_TEAM",
    "PRIVATE_KEY",
    "PRIVATE_KEY_ID",
):
    if not os.environ.get(_var):
        _v = os.environ.get(f"FLASK_{_var}")
        if _v:
            os.environ[_var] = _v

from webapp.app import app

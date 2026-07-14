# This file serves as an entry point for the rock image. It is required by the PaaS app charmer.
# The flask application must be defined in this file under the variable name `app`.
# See - https://documentation.ubuntu.com/rockcraft/en/latest/reference/extensions/flask-framework/

# The actual application lives in webapp/app.py; this re-exports it so that
# the extension can discover the standard `app:app` entrypoint.
import os

# Bridge paas-charm injected env names to the names this app expects.
from canonicalwebteam.flask_base.env import load_plain_env_variables

if not os.environ.get("DATABASE_URL") and os.environ.get("POSTGRESQL_DB_CONNECT_STRING"):
    os.environ["DATABASE_URL"] = os.environ["POSTGRESQL_DB_CONNECT_STRING"]

load_plain_env_variables()

from webapp.app import app

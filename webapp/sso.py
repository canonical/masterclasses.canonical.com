import os
import socket

import flask
from django_openid_auth.teams import TeamsRequest, TeamsResponse
from flask_openid import OpenID

SSO_LOGIN_URL = "https://login.ubuntu.com"
SSO_TEAM = os.getenv("OPENID_LAUNCHPAD_TEAM", "canonical")


def init_sso(app):
    open_id = OpenID(
        store_factory=lambda: None,
        safe_roots=[],
        extension_responses=[TeamsResponse],
    )

    @app.route("/login", methods=["GET", "POST"])
    @open_id.loginhandler
    def login():
        if "openid" in flask.session:
            return flask.redirect(open_id.get_next_url())

        teams_request = TeamsRequest(query_membership=[SSO_TEAM, "canonical-content-people"])
        return open_id.try_login(
            SSO_LOGIN_URL,
            ask_for=["email", "fullname"],
            extensions=[teams_request],
        )

    @open_id.after_login
    def after_login(resp):
        if SSO_TEAM not in resp.extensions["lp"].is_member:
            flask.abort(403)

        flask.session["openid"] = {
            "identity_url": resp.identity_url,
            "email": resp.email,
            "fullname": resp.fullname,
            "is_admin": "canonical-content-people" in resp.extensions["lp"].is_member
        }

        return flask.redirect(open_id.get_next_url())

    @app.route("/logout")
    def logout():
        if "openid" in flask.session:
            flask.session.pop("openid")
        return flask.redirect("/")

    @app.before_request
    def before_request():
        # Get the current path
        path = flask.request.path
        
        # Skip authentication for API routes and specific paths
        if path.startswith("/api/"):
            return
        
        # Skip authentication for other specific paths
        if path in ["/login", "/logout"] or path.startswith("/_status") or path.startswith("/static"):
            return
        
        # Require SSO for all other routes
        if "openid" not in flask.session:
            return flask.redirect("/login?next=" + path)

    @app.after_request
    def add_headers(response):
        """
        Generic rules for headers to add to all requests
        - X-Hostname: Mention the name of the host/pod running the application
        - Cache-Control: Add cache-control headers for public and private pages
        """

        response.headers["X-Hostname"] = socket.gethostname()

        if response.status_code == 200:
            if flask.session:
                response.headers["Cache-Control"] = "private"

        return response

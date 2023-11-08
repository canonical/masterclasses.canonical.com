import flask
from canonicalwebteam.flask_base.app import FlaskBase

from webapp.masterclasses import masterclasses
from webapp.sso import init_sso

app = FlaskBase(
    __name__,
    "masterclasses.canonical.com",
    template_folder="../templates",
    static_folder="../static",
    template_404="404.html",
    template_500="500.html",
)

init_sso(app)

app.register_blueprint(masterclasses, url_prefix="/")


@app.route("/")
def index():
    return flask.render_template("masterclasses.html")

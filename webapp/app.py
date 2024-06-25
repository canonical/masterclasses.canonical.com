import os
import flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from canonicalwebteam.flask_base.app import FlaskBase

from flask_admin import Admin
from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from models.PreviousSession import PreviousSession
from models.UpcomingSession import UpcomingSession
from models.SprintSession import SprintSession


db_engine = create_engine(os.getenv("DATABASE_URL"))
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
)

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


class RestrictedModelView(ModelView):
    # Admin view is accesible to Web&Design team
    def is_accessible(self):
        return flask.session["openid"]["is_admin"] is True


admin = Admin(app)
admin.add_views(
    RestrictedModelView(PreviousSession, db_session),
    RestrictedModelView(UpcomingSession, db_session),
    RestrictedModelView(SprintSession, db_session),
)


@app.route("/")
def index():
    return flask.render_template("masterclasses.html")

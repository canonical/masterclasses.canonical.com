import os
import flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from canonicalwebteam.flask_base.app import FlaskBase
from slugify import slugify as py_slugify
from datetime import datetime, timezone

from webapp.masterclasses import masterclasses
from webapp.sso import init_sso
from webapp.database import db_session
from webapp.admin import (
    Admin, DashboardView, VideoModelView, 
    RestrictedModelView, TagModelView, TagCategoryModelView,
    SubmissionModelView
)
from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from models.submission import VideoSubmission

app = FlaskBase(
    __name__,
    "masterclasses.canonical.com",
    template_folder="../templates",
    static_folder="../static",
    template_404="404.html",
    template_500="500.html",
)

def slugify(text):
    return py_slugify(text)

app.add_template_filter(slugify)

init_sso(app)

app.register_blueprint(masterclasses, url_prefix="/")

# Initialize Flask-Admin
admin = Admin(app, name='Masterclasses Admin', template_mode='bootstrap3', index_view=DashboardView())

# Register models with admin interface
admin.add_view(VideoModelView(Video, db_session))
admin.add_view(RestrictedModelView(Presenter, db_session))
admin.add_view(TagModelView(Tag, db_session))
admin.add_view(TagCategoryModelView(TagCategory, db_session))
admin.add_view(SubmissionModelView(VideoSubmission, db_session))

@app.route("/")
def index():
    return flask.render_template("masterclasses.html")

def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

app.add_template_filter(timestamp_to_date)

@app.template_filter('time_until')
def time_until_filter(timestamp):
    now = datetime.now(timezone.utc)
    event_time = datetime.fromtimestamp(timestamp, timezone.utc)
    diff = event_time - now
    
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    
    return f"{hours}h {minutes}m"

@app.template_filter('format_date')
def format_date_filter(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).strftime('%B %d, %Y')

@app.route("/videos/<video_id>")
def video_player(video_id):
    return flask.render_template("video_player.html", video_id=video_id)
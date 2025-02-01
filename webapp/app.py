import os
import flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from canonicalwebteam.flask_base.app import FlaskBase
from slugify import slugify as py_slugify
from datetime import datetime, timezone
from markdown import markdown

from webapp.masterclasses import masterclasses
from webapp.sso import init_sso
from webapp.database import db_session
from webapp.admin import (
    Admin, DashboardView, VideoModelView, 
    RestrictedModelView, TagModelView, TagCategoryModelView,
    SubmissionModelView, PresenterModelView
)
from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from models.submission import VideoSubmission
from webapp.api import api
from webapp.forms import MasterclassSubmissionForm

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
app.register_blueprint(api, url_prefix="/api")

# Initialize Flask-Admin
admin = Admin(app, name='Masterclasses Admin', template_mode='bootstrap3', index_view=DashboardView())

# Register models with admin interface
admin.add_view(VideoModelView(Video, db_session))
admin.add_view(PresenterModelView(Presenter, db_session))
admin.add_view(TagModelView(Tag, db_session))
admin.add_view(TagCategoryModelView(TagCategory, db_session, name='Tag Categories'))
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

@app.template_filter('markdown')
def markdown_filter(text):
    if not text:
        return ''
    return markdown(text, extensions=['extra'])

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = MasterclassSubmissionForm()
    submission_status = None

    if form.validate_on_submit():
        try:
            # Get the duration value
            duration = form.duration_other.data if form.duration.data == 'other' else form.duration.data
            
            # Create submission
            submission = VideoSubmission(
                title=form.title.data,
                description=form.description.data,
                duration=duration,
                email=session.get('openid', {}).get('email', ''),
                status='pending'
            )
            
            db_session.add(submission)
            db_session.commit()

            submission_status = {
                'success': True,
                'message': 'Your masterclass submission has been received. The team will review it and get back to you soon.'
            }

            # TODO: Add email notification after submission to form has been made.
            # I have started this in ./utils/email.py, but we need a service account before it can be finished.

        except Exception as e:
            db_session.rollback()
            submission_status = {
                'success': False,
                'message': 'There was an error submitting your masterclass. Please try again.'
            }

    return flask.render_template(
        "register.html",
        form=form,
        submission_status=submission_status
    )
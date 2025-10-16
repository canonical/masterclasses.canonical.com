import os
import flask
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from canonicalwebteam.flask_base.app import FlaskBase
from slugify import slugify as py_slugify
from datetime import datetime, timezone
from markdown import markdown
from flask_apscheduler import APScheduler
from scripts.update_presenters import update_presenters
from apscheduler.schedulers.background import BackgroundScheduler
from zoneinfo import ZoneInfo

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
from canonicalwebteam import image_template
from jinja2 import ChoiceLoader, FileSystemLoader
from sqlalchemy.sql.expression import func, and_

app = FlaskBase(
    __name__,
    "masterclasses.canonical.com",
    template_folder="../templates",
    static_folder="../static",
    template_404="404.html",
    template_500="500.html",
)

# Allow loading pattern templates from Vanilla
loader = ChoiceLoader([
    FileSystemLoader('templates'),
    FileSystemLoader('node_modules/vanilla-framework/templates/')
])
app.jinja_loader = loader

@app.context_processor
def utility_processor():
    return {"image": image_template}

# Initialize scheduler with explicit timezone
background_scheduler = BackgroundScheduler(
    timezone=ZoneInfo('Europe/London')
)
scheduler = APScheduler(scheduler=background_scheduler)
app.config['SCHEDULER_API_ENABLED'] = True
scheduler.init_app(app)

# Add scheduled job to run immediately and then every 60 minutes
@scheduler.task(
    'interval',
    id='update_presenters',
    days=1,
    next_run_time=datetime.now(ZoneInfo('Europe/London'))  # Run immediately on startup
)
def scheduled_update_presenters():
    try:
        update_presenters()
    except Exception as e:
        app.logger.error(f"Failed to update presenters: {e}")

# Start the scheduler
scheduler.start()

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

@app.template_filter('format_date_iso')
def format_date_filter_iso(timestamp):
    """Convert a UNIX timestamp to ISO 8601 string in UTC."""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

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


@app.route("/events/<event_slug>")
def event_detail(event_slug):
    yaml_path = os.path.join("events", f"{event_slug}.yaml")

    if not os.path.exists(yaml_path):
        flask.abort(404, description="Event not found")

    try:
        with open(yaml_path, "r") as f:
            event_data = yaml.safe_load(f)
    except (IOError, yaml.YAMLError) as e:
        app.logger.error(f"Failed to read or parse YAML for '{event_slug}': {e}")
        flask.abort(500, description="Invalid or unreadable event data")

    tag_name = event_data.get("tag")

    # TODO: Read featured video from YAML when available (timestamp?)
    featured_video = None

    # For each session, find videos within its time range
    for day in event_data.get("days", []):
        for session in day.get("sessions", []):
            start_datetime = session.get("start")
            end_datetime = session.get("end")

            if not start_datetime or not end_datetime:
                session["videos"] = []
                app.logger.warning(f"Session '{session.get('title')}' is missing start or end time in '{event_slug}'.")
                continue

            if not isinstance(start_datetime, datetime):
                raise TypeError(f"Value of 'start' must be a valid datetime, got {start_datetime!r}.")

            if not isinstance(end_datetime, datetime):
                raise TypeError(f"Value of 'end' must be a valid datetime, got {end_datetime!r}.")

            # Convert to epoch seconds
            start_ts = int(start_datetime.timestamp())
            end_ts = int(end_datetime.timestamp())

            # Query videos filtered by tag first (if provided)
            query = db_session.query(Video).join(Video.tags)
            if tag_name:
                query = query.filter(Tag.name == tag_name)

            # Filter videos where 'unixstart' is within the session's time range
            session_videos = query.filter(
                Video.unixstart >= start_ts,
                Video.unixstart < end_ts
            ).order_by(Video.unixstart).all()

            # Use last video as featured video (should end up as "Closing plenary")
            # TODO: fix this when we have a proper way to mark featured video
            if session_videos:
                featured_video = session_videos[-1]

            session["videos"] = session_videos


    if featured_video:
        event_data["featured_video"] = featured_video

    return flask.render_template("event.html", event=event_data)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

import os
import flask
from sqlalchemy import create_engine, func, nullslast
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime

from models.PreviousSession import PreviousSession
from models.UpcomingSession import UpcomingSession
from models.SprintSession import SprintSession

db_engine = create_engine(os.getenv("DATABASE_URL"))
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
)


masterclasses = flask.Blueprint(
    "masterclasses",
    __name__,
    template_folder="/templates",
    static_folder="/static",
)


@masterclasses.route("/")
def index():
    previous_sessions = get_previous_sessions()
    upcoming_sessions = get_upcoming_sessions()
    sprint_sessions = get_sprint_sessions()
    tags = get_tags()

    return flask.render_template(
        "masterclasses.html",
        previous_sessions=previous_sessions,
        upcoming_sessions=upcoming_sessions,
        sprint_sessions=sprint_sessions,
        tags=tags,
    )

@masterclasses.route("/<title>-class-<id>")
def previous_video(id,title):
    session = get_session_by_id(id, "previous")
    return flask.render_template("video.html", session=session)

@masterclasses.route("/<title>-sprint-<id>")
def sprint_video(id,title):
    session = get_session_by_id(id, "sprint")
    return flask.render_template("video.html", session=session)


def get_video_id(url):
    if "drive.google.com/file/d/" in url:
        return url.split("/")[-2]
    elif "drive.google.com/open?id=" in url:
        return url.split("=")[-1]
    else:
        return url

def format_date(date):
    # change the date format, like 23 May 2024
    if isinstance(date, str):
        # If date is already a string, try to parse it
        try:
            date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            # If parsing fails, return the original string
            return date
    return date.strftime("%d %b %Y")

def enrich_session(session):
    session.date = format_date(session.date)
    session.video_id = get_video_id(session.recording)
    return session


def get_upcoming_sessions():
    upcoming_sessions = (
        db_session.query(UpcomingSession)
        .order_by(nullslast(UpcomingSession.date.desc()))
        .all()
    )
    for s in upcoming_sessions:
        s.date = format_date(s.date)
    return upcoming_sessions

def get_previous_sessions():
    previous_sessions = (
        db_session.query(PreviousSession).order_by(PreviousSession.date.desc()).all()
    )
    return [enrich_session(s) for s in previous_sessions]

def get_sprint_sessions():
    sprint_sessions = db_session.query(SprintSession).order_by(SprintSession.date.desc()).all()
    return [enrich_session(s) for s in sprint_sessions]


def get_session_by_id(id, session_type):
    if session_type == "previous":
        session = (
            db_session.query(PreviousSession)
            .filter(PreviousSession.id == id)
            .first()
        )
    elif session_type == "sprint":
        session = (
            db_session.query(SprintSession)
            .filter(SprintSession.id == id)
            .first()
        )
    return enrich_session(session)


def get_tags():
    tag_counts = (
        db_session.query(PreviousSession.tags, func.count(PreviousSession.tags))
        .filter(PreviousSession.tags.isnot(None))
        .group_by(PreviousSession.tags)
        .all()
    )
    tags = {}
    for tag, count in tag_counts:
        for t in tag.split(","):
            t = t.strip()
            if t:
                if t not in tags:
                    tags[t] = count
                else:
                    tags[t] += count
    return tags

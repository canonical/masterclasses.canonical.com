import os
import flask
from sqlalchemy import create_engine, func, nullslast
from sqlalchemy.orm import scoped_session, sessionmaker

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


def format_date(date):
    # change the date format, like 23 May 2024
    return date.strftime("%d %b %Y")


def get_upcoming_sessions():
    session = (
        db_session.query(UpcomingSession)
        .order_by(nullslast(UpcomingSession.date.desc()))
        .all()
    )
    for i in range(len(session)):
        if session[i].date:
            session[i].date = format_date(session[i].date)
    return session


def get_previous_sessions():
    session = (
        db_session.query(PreviousSession).order_by(PreviousSession.date.desc()).all()
    )
    for i in range(len(session)):
        session[i].date = format_date(session[i].date)
    return session


def get_sprint_sessions():
    session = db_session.query(SprintSession).order_by(SprintSession.date.desc()).all()
    return session


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

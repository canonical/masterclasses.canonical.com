import os
import flask
from sqlalchemy import create_engine, func, nullslast, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime, timezone

from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory

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
    now = datetime.now(timezone.utc)
    now_unix = int(now.timestamp())
    
    # Live videos (started but not ended)
    live_videos = db_session.query(Video).filter(
        and_(
            Video.unixstart <= now_unix,
            Video.unixend >= now_unix
        )
    ).all()

    # Videos in next 24 hours
    upcoming_videos_24h = db_session.query(Video).filter(
        and_(
            Video.unixstart > now_unix,
            Video.unixstart <= now_unix + 86400  # 24 hours in seconds
        )
    ).order_by(Video.unixstart).all()

    # Future videos (beyond 24 hours)
    upcoming_videos_future = db_session.query(Video).filter(
        Video.unixstart > now_unix + 86400
    ).order_by(Video.unixstart).all()

    # Query tag categories and their associated tags
    topic_tags = db_session.query(Tag).join(TagCategory).filter(TagCategory.name == "Topic").all()
    event_tags = db_session.query(Tag).join(TagCategory).filter(TagCategory.name == "Event").all()
    date_tags = db_session.query(Tag).join(TagCategory).filter(TagCategory.name == "Date").all()
    presenters = db_session.query(Presenter).all()

    return flask.render_template(
        "masterclasses.html",
        live_videos=live_videos,
        upcoming_videos_24h=upcoming_videos_24h,
        upcoming_videos_future=upcoming_videos_future,
        topic_tags=topic_tags,
        event_tags=event_tags,
        date_tags=date_tags,
        presenters=presenters,
        now=now_unix
    )

@masterclasses.route("/<title>-class-<id>")
def video(id, title):
    video = get_video_by_id(id)
    if not video:
        flask.abort(404)
        
    # Verify the title slug matches
    if flask.current_app.jinja_env.filters['slugify'](video.title) != title:
        return flask.redirect(
            flask.url_for(
                'masterclasses.video',
                title=flask.current_app.jinja_env.filters['slugify'](video.title),
                id=id
            )
        )
    
    return flask.render_template("video.html", video=video)

@masterclasses.route("/videos")
def videos():
    now = datetime.now(timezone.utc)
    now_unix = int(now.timestamp())
    
    # First get videos with recordings
    videos = db_session.query(Video).filter(Video.recording.isnot(None)).all()
    
    # Get tags and presenters only for videos that have recordings
    video_ids = [v.id for v in videos]
    
    # Query tags only for videos with recordings
    topic_tags = (db_session.query(Tag)
                 .join(TagCategory)
                 .join(Tag.videos)
                 .filter(TagCategory.name == "Topic")
                 .filter(Video.id.in_(video_ids))
                 .filter(Video.recording.isnot(None))
                 .distinct()
                 .all())
    
    event_tags = (db_session.query(Tag)
                 .join(TagCategory)
                 .join(Tag.videos)
                 .filter(TagCategory.name == "Event")
                 .filter(Video.id.in_(video_ids))
                 .filter(Video.recording.isnot(None))
                 .distinct()
                 .all())
    
    date_tags = (db_session.query(Tag)
                .join(TagCategory)
                .join(Tag.videos)
                .filter(TagCategory.name == "Date")
                .filter(Video.id.in_(video_ids))
                .filter(Video.recording.isnot(None))
                .distinct()
                .all())
    
    # Get presenters only for videos with recordings
    presenters = (db_session.query(Presenter)
                 .join(Presenter.videos)
                 .filter(Video.id.in_(video_ids))
                 .filter(Video.recording.isnot(None))
                 .distinct()
                 .all())

    return flask.render_template(
        "videos.html",
        videos=videos,
        topic_tags=topic_tags,
        event_tags=event_tags,
        date_tags=date_tags,
        presenters=presenters,
        now=now_unix
    )

@masterclasses.app_template_filter()
def timestamp_to_date(value, format='%d %b %Y'):
    """Convert unix timestamp to formatted date string."""
    if not value:
        return ''
    try:
        return datetime.fromtimestamp(int(value)).strftime(format)
    except (ValueError, TypeError):
        return ''
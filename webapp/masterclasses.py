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

    # Get live videos for navigation (unfiltered)
    live_videos = db_session.query(Video).filter(
        and_(
            Video.unixstart <= now_unix,
            Video.unixend >= now_unix
        )
    ).all()
    
    # First get videos with recordings
    recorded_videos = db_session.query(Video).filter(Video.recording.isnot(None)).all()
    
    # Get tags and presenters only for videos that have recordings
    video_ids = [v.id for v in recorded_videos]
    
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
        recorded_videos=recorded_videos,
        live_videos=live_videos,
        topic_tags=topic_tags,
        event_tags=event_tags,
        date_tags=date_tags,
        presenters=presenters,
        now=now_unix
    )

@masterclasses.route("/videos/<title>-class-<id>")
def video_player(title, id):
    video = db_session.query(Video)\
        .filter(Video.id == id)\
        .first()
    
    if not video:
        flask.abort(404)
        
    # Verify the title slug matches
    if flask.current_app.jinja_env.filters['slugify'](video.title) != title:
        return flask.redirect(
            flask.url_for(
                'masterclasses.video_player',
                title=flask.current_app.jinja_env.filters['slugify'](video.title),
                id=id
            )
        )
    
    # Get topic tags for the current video
    topic_tags = [tag.id for tag in video.tags if tag.category.name == "Topic"]
    
    # Base query for suggested videos
    suggested_query = db_session.query(Video)\
        .filter(Video.id != video.id)\
        .filter(Video.recording.isnot(None))

    if topic_tags:
        # If we have topic tags, try to find videos with matching tags
        suggested_videos = suggested_query\
            .join(Tag, Video.tags)\
            .join(TagCategory)\
            .filter(TagCategory.name == "Topic")\
            .filter(Tag.id.in_(topic_tags))\
            .group_by(Video.id)\
            .order_by(func.count(Tag.id).desc())\
            .limit(3)\
            .all()
    else:
        # If no topic tags, just get recent videos
        suggested_videos = suggested_query\
            .order_by(Video.unixstart.desc())\
            .limit(3)\
            .all()

    # If still no suggestions, get random videos
    if not suggested_videos:
        suggested_videos = suggested_query\
            .order_by(func.random())\
            .limit(3)\
            .all()
    
    return flask.render_template(
        "video_player.html",
        video=video,
        suggested_videos=suggested_videos
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

@masterclasses.app_template_filter('google_drive_id')
def google_drive_id(url):
    """Extract Google Drive ID from URL."""
    if not url:
        return ''
    try:
        # Handle URLs in format: https://drive.google.com/file/d/FILEID/view?usp=sharing
        return url.split('/d/')[1].split('/')[0]
    except (IndexError, AttributeError):
        return url

@masterclasses.route("/random")
def random_video():
    video = db_session.query(Video)\
        .filter(Video.recording.isnot(None))\
        .order_by(func.random())\
        .first()
    
    if not video:
        return flask.redirect(flask.url_for('masterclasses.videos'))
        
    return flask.redirect(
        flask.url_for(
            'masterclasses.video_player',
            title=flask.current_app.jinja_env.filters['slugify'](video.title),
            id=video.id
        )
    )
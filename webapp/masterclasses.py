import logging
import os
from datetime import datetime, timezone

import flask
from sqlalchemy import and_, func

from models.presenter import Presenter
from models.submission import VideoSubmission
from models.tag import Tag, TagCategory
from models.video import Video
from webapp.database import db_session
from webapp.forms import MasterclassRegistrationForm
from webapp.mattermost import MattermostMessagePayload, try_send_message
from webapp.services.video_service import VideoService

masterclasses = flask.Blueprint(
    "masterclasses",
    __name__,
    template_folder="/templates",
    static_folder="/static",
)

logger = logging.getLogger(__name__)


def get_live_videos():
    """Helper function to get currently live videos."""
    now = datetime.now(timezone.utc)
    now_unix = int(now.timestamp())

    return db_session.query(Video).filter(
        and_(
            Video.unixstart <= now_unix,
            Video.unixend >= now_unix
        )
    ).all()


def get_tags_by_category(category_name):
    """Helper function to get tags by category name that have associated videos with recordings."""
    query = (db_session.query(Tag)
             .join(TagCategory)
             .join(Tag.videos)  # Join with videos
             .filter(TagCategory.name == category_name)
             # Only count videos with recordings
             .filter(Video.recording.isnot(None))
             .group_by(Tag.id, TagCategory.id)  # Group by to avoid duplicates
             # Only include tags with at least one video
             .having(func.count(Video.id) > 0))

    if category_name == 'Date':
        # For date tags, we'll sort them in reverse chronological order
        tags = query.all()

        def date_sort_key(tag):
            # Parse "Q1 2024" format
            quarter = int(tag.name[1])  # Get the quarter number
            year = int(tag.name[-4:])   # Get the year
            return (-year, -quarter)     # Negative for reverse order

        return sorted(tags, key=date_sort_key)
    else:
        # For other categories, sort alphabetically
        return query.order_by(Tag.name).all()


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
    topic_tags = db_session.query(Tag).join(
        TagCategory).filter(TagCategory.name == "Topic").all()
    event_tags = db_session.query(Tag).join(
        TagCategory).filter(TagCategory.name == "Event").all()
    date_tags = db_session.query(Tag).join(
        TagCategory).filter(TagCategory.name == "Date").all()
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
    video_service = VideoService()
    video = video_service.get_video_by_id(id)
    if not video:
        flask.abort(404)

    # Verify the title slug matches
    if flask.current_app.jinja_env.filters['slugify'](video.title) != title:
        return flask.redirect(
            flask.url_for(
                'masterclasses.video',
                title=flask.current_app.jinja_env.filters['slugify'](
                    video.title),
                id=id
            )
        )

    return flask.render_template("video.html", video=video)


@masterclasses.route("/videos")
def videos():
    # Get pagination parameters from request
    page = flask.request.args.get('page', 1, type=int)
    items_per_page = 12
    
    topic_filter_slugs = flask.request.args.get('topic', '').split(',')
    event_filter_slugs = flask.request.args.get('event', '').split(',')
    date_filter_slugs = flask.request.args.get('date', '').split(',')
    presenter_filter_slugs = flask.request.args.get('presenter', '').split(',')
    
    topic_filter_slugs = [f for f in topic_filter_slugs if f]
    event_filter_slugs = [f for f in event_filter_slugs if f]
    date_filter_slugs = [f for f in date_filter_slugs if f]
    presenter_filter_slugs = [f for f in presenter_filter_slugs if f]

    all_tags = db_session.query(Tag).all()
    slugify = flask.current_app.jinja_env.filters['slugify']
    
    tag_slug_to_id = {slugify(tag.name): tag.id for tag in all_tags}
    
    topic_filter = [tag_slug_to_id.get(slug) for slug in topic_filter_slugs if slug in tag_slug_to_id]
    event_filter = [tag_slug_to_id.get(slug) for slug in event_filter_slugs if slug in tag_slug_to_id]
    date_filter = [tag_slug_to_id.get(slug) for slug in date_filter_slugs if slug in tag_slug_to_id]
    
    all_presenters = db_session.query(Presenter).all()
    presenter_slug_to_id = {slugify(presenter.name): presenter.id for presenter in all_presenters}
    presenter_filter = [presenter_slug_to_id.get(slug) for slug in presenter_filter_slugs if slug in presenter_slug_to_id]

    
    video_service = VideoService()
    topic_tags = video_service.get_tags_by_category('Topic')
    event_tags = video_service.get_tags_by_category('Event')
    date_tags = video_service.get_tags_by_category('Date')
    presenters = video_service.get_presenters_with_videos()
    live_videos = video_service.get_live_videos()
    
    search_query = flask.request.args.get('search', '')
    
    # Get filtered videos using the service
    recorded_videos, total_videos = video_service.search_videos(
        search_query,
        topic_filter,
        event_filter,
        date_filter,
        presenter_filter,
        page,
        items_per_page
    )
    
    total_pages = max(1, (total_videos + items_per_page - 1) // items_per_page)
    page = min(max(1, page), total_pages)
    
    active_filter_slugs = {
        'topic': topic_filter_slugs,
        'event': event_filter_slugs,
        'date': date_filter_slugs,
        'presenter': presenter_filter_slugs
    }

    return flask.render_template(
        "videos.html",
        recorded_videos=recorded_videos,
        topic_tags=topic_tags,
        event_tags=event_tags,
        date_tags=date_tags,
        presenters=presenters,
        live_videos=live_videos,
        pagination={
            'page': page,
            'total_pages': total_pages,
            'total_items': total_videos,
            'items_per_page': items_per_page
        },
        active_filters={
            'topic': topic_filter,
            'event': event_filter,
            'date': date_filter,
            'presenter': presenter_filter,
            'search': search_query
        },
        active_filter_slugs=active_filter_slugs
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
                title=flask.current_app.jinja_env.filters['slugify'](
                    video.title),
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

    # Get live videos using helper function
    live_videos = get_live_videos()

    return flask.render_template(
        "video_player.html",
        video=video,
        suggested_videos=suggested_videos,
        live_videos=live_videos
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


@masterclasses.route("/register", methods=["GET", "POST"])
def register():
    live_videos = get_live_videos()

    form = MasterclassRegistrationForm()
    submission_status = None

    if form.validate_on_submit():
        try:
            submission = VideoSubmission(
                title=form.title.data,
                description=form.description.data,
                duration=form.duration_other.data if form.duration.data == 'other' else form.duration.data,
                email=flask.session["openid"]["email"]
            )

            db_session.add(submission)
            db_session.commit()
            # TODO: Add email notification after submission to form has been made.
            # I have started this in ./utils/email.py, but we need a service account before it can be finished.
            # TODO: Integrate with Celery to send the message in the background.
            # This works for now but with adding email notifications, we need to send the message in the background instead of increasing the request time.
            notification_text = (
                "### 🎉 New masterclass submission 🎉\n"
                f"**Title:** {form.title.data}\n"
                f"**Description:**\n{form.description.data}\n"
                f"**Duration:** {form.duration.data}\n"
                f"**Email:** {flask.session['openid']['email']}"
            )
            mattermost_message = MattermostMessagePayload(
                text=notification_text
            )
            mattermost_url = os.getenv('MATTERMOST_DEV_WEBHOOK_URL')
            if mattermost_url:
                try_send_message(
                    mattermost_message, mattermost_url)
            # Clear the form after successful submission
            form = MasterclassRegistrationForm(None)
            submission_status = {
                'success': True,
                'message': "Your masterclass submission has been received successfully! We'll review it and get back to you soon."
            }

        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to save submission: {e}")
            submission_status = {
                'success': False,
                'message': "There was an error submitting your masterclass. Please try again."
            }

    return flask.render_template(
        "register.html",
        form=form,
        submission_status=submission_status,
        live_videos=live_videos
    )

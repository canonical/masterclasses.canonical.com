import os
import flask
from sqlalchemy import create_engine, func, nullslast, and_, or_
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime, timezone
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from unidecode import unidecode

from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from webapp.database import db_session
from webapp.forms import MasterclassRegistrationForm
from models.submission import VideoSubmission
from webapp.auth import require_api_token
from flask import jsonify

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
            .filter(Video.recording.isnot(None))  # Only count videos with recordings
            .group_by(Tag.id, TagCategory.id)  # Group by to avoid duplicates
            .having(func.count(Video.id) > 0))  # Only include tags with at least one video
    
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
    # Get pagination parameters from request
    page = flask.request.args.get('page', 1, type=int)
    items_per_page = 12
    
    # Get filter parameters as slugs
    topic_filter_slugs = flask.request.args.get('topic', '').split(',') if flask.request.args.get('topic') else []
    event_filter_slugs = flask.request.args.get('event', '').split(',') if flask.request.args.get('event') else []
    date_filter_slugs = flask.request.args.get('date', '').split(',') if flask.request.args.get('date') else []
    presenter_filter_slugs = flask.request.args.get('presenter', '').split(',') if flask.request.args.get('presenter') else []
    
    # Remove empty values from filters
    topic_filter_slugs = [f for f in topic_filter_slugs if f]
    event_filter_slugs = [f for f in event_filter_slugs if f]
    date_filter_slugs = [f for f in date_filter_slugs if f]
    presenter_filter_slugs = [f for f in presenter_filter_slugs if f]
    
    # Convert slugs to IDs by looking up in the database
    # For tags (topic, event, date)
    all_tags = db_session.query(Tag).all()
    slugify = flask.current_app.jinja_env.filters['slugify']
    
    # Create slug to ID mappings
    tag_slug_to_id = {slugify(tag.name): tag.id for tag in all_tags}
    
    # Convert slugs to IDs for each filter type
    topic_filter = [tag_slug_to_id.get(slug) for slug in topic_filter_slugs if slug in tag_slug_to_id]
    event_filter = [tag_slug_to_id.get(slug) for slug in event_filter_slugs if slug in tag_slug_to_id]
    date_filter = [tag_slug_to_id.get(slug) for slug in date_filter_slugs if slug in tag_slug_to_id]
    
    # For presenters
    all_presenters = db_session.query(Presenter).all()
    presenter_slug_to_id = {slugify(presenter.name): presenter.id for presenter in all_presenters}
    presenter_filter = [presenter_slug_to_id.get(slug) for slug in presenter_filter_slugs if slug in presenter_slug_to_id]
    
    # Get all videos (unfiltered) for client-side filtering
    all_videos_query = (
        db_session.query(Video)
        .filter(Video.recording.isnot(None))
        .order_by(Video.unixstart.desc())
    )
    all_recorded_videos = all_videos_query.all()
    
    # Get all tags by category
    topic_tags = get_tags_by_category('Topic')
    event_tags = get_tags_by_category('Event')
    date_tags = get_tags_by_category('Date')
    
    # Get only presenters who have videos with recordings
    presenters = (db_session.query(Presenter)
                 .join(Presenter.videos)
                 .filter(Video.recording.isnot(None))
                 .group_by(Presenter.id)
                 .having(func.count(Video.id) > 0)
                 .order_by(Presenter.name)
                 .all())
    
    # Get live videos using helper function
    live_videos = get_live_videos()
    
    # Get search query parameter
    search_query = flask.request.args.get('search', '')
    
    # Helper function to render the empty results template
    def render_empty_results():
        return flask.render_template(
            "videos.html",
            recorded_videos=[],
            all_recorded_videos=all_recorded_videos,
            topic_tags=topic_tags,
            event_tags=event_tags,
            date_tags=date_tags,
            presenters=presenters,
            live_videos=live_videos,
            pagination={'page': 1, 'total_pages': 1, 'total_items': 0, 'items_per_page': items_per_page},
            active_filters={
                'topic': topic_filter,
                'event': event_filter,
                'date': date_filter,
                'presenter': presenter_filter
            }
        )

    # Base query for videos with recordings
    query_base = db_session.query(Video).filter(Video.recording.isnot(None))
    
    # Create a set of matched video IDs, initially None (meaning "all videos")
    matched_ids = None
    
    # Define a function to execute a filter query and update matched_ids
    def apply_filter(filter_query):
        nonlocal matched_ids
        # Get IDs from this filter
        filter_ids = {vid.id for vid in filter_query}
        # If this is the first filter, set matched_ids to this set
        # Otherwise, take the intersection with existing matched_ids
        if matched_ids is None:
            matched_ids = filter_ids
        else:
            matched_ids &= filter_ids
        # If no videos match after this filter, we can return early
        return len(matched_ids) > 0
    
    # Apply tag filters (topic, event, date)
    tag_filters = [
        ('Topic', topic_filter),
        ('Event', event_filter),
        ('Date', date_filter)
    ]
    
    # Apply tag filters
    for category, filter_values in tag_filters:
        if filter_values:
            # Create a query for this tag category
            tag_query = (
                query_base.join(Tag, Video.tags)
                .join(TagCategory)
                .filter(TagCategory.name == category)
                .filter(Tag.id.in_(filter_values))
                .distinct()
            )
            # Apply the filter and return empty results if no matches
            if not apply_filter(tag_query):
                return render_empty_results()
    
    # Apply presenter filter
    if presenter_filter:
        presenter_query = (
            query_base.join(Video.presenters)
            .filter(Presenter.id.in_(presenter_filter))
            .distinct()
        )
        if not apply_filter(presenter_query):
            return render_empty_results()
    
    # Apply search filter if provided
    if search_query:
        # Normalize the search query to remove diacritics
        normalized_search = unidecode(search_query.lower())
        search_terms = normalized_search.split()
        
        # Create a query for matching videos by tag, presenter, title, or description
        search_query_obj = (
            query_base
            .outerjoin(Tag, Video.tags)
            .outerjoin(Video.presenters)
            .group_by(Video.id)
            .having(
                or_(
                    # Match by presenter name using simple contains
                    func.lower(func.string_agg(Presenter.name, ' ')).contains(search_query.lower()),
                    
                    # Match by tag name
                    func.lower(func.string_agg(Tag.name, ' ')).contains(search_query.lower()),
                    
                    # Match by video title or description
                    *[
                        or_(
                            func.lower(Video.title).contains(term),
                            func.lower(Video.description).contains(term)
                        ) for term in search_terms
                    ]
                )
            )
        )
        
        # Apply the search filter (modifies matched_ids)
        if not apply_filter(search_query_obj):
            # Always search ALL videos with recordings if no direct database matches
            all_videos = db_session.query(Video).filter(Video.recording.isnot(None)).all()
            
            # Filter in Python with a more flexible approach
            filtered_ids = set()
            
            # Create search tokens for more flexible matching
            search_tokens = normalize_and_tokenize(search_query)
            
            for video in all_videos:
                # Check presenters - this is our primary focus
                for presenter in video.presenters:
                    presenter_name = presenter.name.lower()
                    normalized_presenter = unidecode(presenter_name)
                    
                    # Check if any part of the presenter's name contains the search term
                    if normalized_search in normalized_presenter:
                        filtered_ids.add(video.id)
                        break
                    
                    # Additional check for name parts
                    name_parts = normalized_presenter.split()
                    
                    # Special handling for partial surname matches
                    for part in name_parts:
                        if part.startswith(normalized_search) or normalized_search.startswith(part):
                            filtered_ids.add(video.id)
                            break
                            
                        # Check if the search term is anywhere in any name part 
                        if normalized_search in part:
                            filtered_ids.add(video.id)
                            break
            
            # Use the Python-filtered results directly if we found any
            if filtered_ids:
                matched_ids = filtered_ids
    
    # If no filters were applied, matched_ids is still None, meaning we want all videos
    if matched_ids is None:
        final_query = query_base
    else:
        final_query = query_base.filter(Video.id.in_(matched_ids))
    
    # Order and paginate results
    final_query = final_query.order_by(Video.unixstart.desc())
    total_videos = final_query.count()
    total_pages = max(1, (total_videos + items_per_page - 1) // items_per_page)
    
    # Ensure page is in valid range
    page = min(max(1, page), total_pages)
    
    # Get paginated videos
    recorded_videos = final_query.limit(items_per_page).offset((page - 1) * items_per_page).all()
    
    # Create a dictionary for active filter slugs for template use
    active_filter_slugs = {
        'topic': topic_filter_slugs,
        'event': event_filter_slugs,
        'date': date_filter_slugs,
        'presenter': presenter_filter_slugs
    }
    
    return flask.render_template(
        "videos.html",
        recorded_videos=recorded_videos,
        all_recorded_videos=all_recorded_videos,
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
        active_filter_slugs=active_filter_slugs  # Pass slugs to template
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
    if "openid" not in flask.session:
        return flask.redirect("/login?next=/register")
    
    # Get live videos using helper function
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

def normalize_and_tokenize(text):
    """
    Normalize text by removing diacritics and tokenize it into individual words, 
    subwords, and combined forms to improve partial matching.
    """
    if not text:
        return []
    
    # Normalize to remove diacritics
    normalized = unidecode(text.lower()).strip()
    
    # Tokenize by splitting on spaces and other separators
    words = normalized.replace('-', ' ').replace('_', ' ').split()
    
    # Start with the full normalized text and individual words
    tokens = [normalized] + words
    
    # Add combined versions for multi-word names
    if len(words) > 1:
        tokens.append(''.join(words))
    
    # Generate substrings for each word (minimum 3 characters)
    subwords = []
    for word in words:
        if len(word) >= 3:
            # Add the word itself and all substrings of at least 3 chars
            for i in range(len(word) - 2):
                for j in range(i + 3, len(word) + 1):
                    subwords.append(word[i:j])
    
    # Add all unique tokens
    tokens.extend(subwords)
    
    return list(set(tokens))
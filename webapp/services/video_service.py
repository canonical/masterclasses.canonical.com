from datetime import datetime, timezone
from sqlalchemy import func, and_, or_
from webapp.database import db_session
from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from webapp.utils.text_utils import slugify
from unidecode import unidecode

class VideoService:
    @staticmethod
    def get_live_videos():
        """Get currently live videos."""
        now = datetime.now(timezone.utc)
        now_unix = int(now.timestamp())
        
        return db_session.query(Video).filter(
            and_(
                Video.unixstart <= now_unix,
                Video.unixend >= now_unix
            )
        ).all()

    @staticmethod
    def get_tags_by_category(category_name):
        """Get tags by category name that have associated videos with recordings."""
        query = (db_session.query(Tag)
                .join(TagCategory)
                .join(Tag.videos)
                .filter(TagCategory.name == category_name)
                .filter(Video.recording.isnot(None))
                .group_by(Tag.id, TagCategory.id)
                .having(func.count(Video.id) > 0))
        
        if category_name == 'Date':
            tags = query.all()
            def date_sort_key(tag):
                quarter = int(tag.name[1])
                year = int(tag.name[-4:])
                return (-year, -quarter)
            return sorted(tags, key=date_sort_key)
        else:
            return query.order_by(Tag.name).all()

    @staticmethod
    def get_presenters_with_videos():
        """Get presenters who have recorded videos."""
        return (db_session.query(Presenter)
                .join(Presenter.videos)
                .filter(Video.recording.isnot(None))
                .group_by(Presenter.id)
                .having(func.count(Video.id) > 0)
                .order_by(Presenter.name)
                .all())

    @staticmethod
    def search_videos(search_query, topic_filter, event_filter, date_filter, presenter_filter, page, items_per_page):
        """Search videos with filters and pagination."""
        query_base = db_session.query(Video).filter(Video.recording.isnot(None))
        matched_ids = None

        def apply_filter(filter_query):
            nonlocal matched_ids
            filter_ids = {vid.id for vid in filter_query}
            if matched_ids is None:
                matched_ids = filter_ids
            else:
                matched_ids &= filter_ids
            return len(matched_ids) > 0

        tag_filters = [
            ('Topic', topic_filter),
            ('Event', event_filter),
            ('Date', date_filter)
        ]
        
        for category, filter_values in tag_filters:
            if filter_values:
                tag_query = (
                    query_base.join(Tag, Video.tags)
                    .join(TagCategory)
                    .filter(TagCategory.name == category)
                    .filter(Tag.id.in_(filter_values))
                    .distinct()
                )
                if not apply_filter(tag_query):
                    return [], 0

        if presenter_filter:
            presenter_query = (
                query_base.join(Video.presenters)
                .filter(Presenter.id.in_(presenter_filter))
                .distinct()
            )
            if not apply_filter(presenter_query):
                return [], 0

        if search_query:
            normalized_search = unidecode(search_query.lower())
            search_terms = normalized_search.split()
            
            search_query_obj = (
                query_base
                .outerjoin(Tag, Video.tags)
                .outerjoin(Video.presenters)
                .group_by(Video.id)
                .having(
                    or_(
                        func.lower(func.string_agg(Presenter.name, ' ')).contains(search_query.lower()),
                        func.lower(func.string_agg(Tag.name, ' ')).contains(search_query.lower()),
                        *[
                            or_(
                                func.lower(Video.title).contains(term),
                                func.lower(Video.description).contains(term)
                            ) for term in search_terms
                        ]
                    )
                )
            )
            
            if not apply_filter(search_query_obj):
                all_videos = db_session.query(Video).filter(Video.recording.isnot(None)).all()
                filtered_ids = set()
                
                search_tokens = slugify(search_query)
                
                for video in all_videos:
                    for presenter in video.presenters:
                        presenter_name = presenter.name.lower()
                        normalized_presenter = unidecode(presenter_name)
                        
                        if normalized_search in normalized_presenter:
                            filtered_ids.add(video.id)
                            break
                        
                        name_parts = normalized_presenter.split()
                        
                        for part in name_parts:
                            if part.startswith(normalized_search) or normalized_search.startswith(part):
                                filtered_ids.add(video.id)
                                break
                                
                            if normalized_search in part:
                                filtered_ids.add(video.id)
                                break
                
                if filtered_ids:
                    matched_ids = filtered_ids

        if matched_ids is None:
            final_query = query_base
        else:
            final_query = query_base.filter(Video.id.in_(matched_ids))
        
        final_query = final_query.order_by(Video.unixstart.desc())
        total_videos = final_query.count()
        
        # Apply pagination
        videos = final_query.limit(items_per_page).offset((page - 1) * items_per_page).all()
        
        return videos, total_videos 
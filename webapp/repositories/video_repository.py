from datetime import datetime, timezone
from sqlalchemy import func, and_, or_
from webapp.database import db_session
from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory

class VideoRepository:
    @staticmethod
    def get_live_videos():
        now = datetime.now(timezone.utc)
        now_unix = int(now.timestamp())
        
        return db_session.query(Video).filter(
            and_(
                Video.unixstart <= now_unix,
                Video.unixend >= now_unix
            )
        ).all()

    @staticmethod
    def get_all_recorded_videos():
        """Get all videos that have recordings."""
        return (db_session.query(Video)
                .filter(Video.recording.isnot(None))
                .order_by(Video.unixstart.desc())
                .all())

    @staticmethod
    def get_videos_by_ids(video_ids):
        return db_session.query(Video).filter(Video.id.in_(video_ids)).all()

    @staticmethod
    def get_videos_with_filters(base_query, filters):
        query = base_query
        for filter_query in filters:
            query = query.filter(filter_query)
        return query.all()

    @staticmethod
    def get_videos_with_pagination(query, page, items_per_page):
        return query.limit(items_per_page).offset((page - 1) * items_per_page).all()

    @staticmethod
    def get_videos_count(query):
        return query.count()

    @staticmethod
    def get_videos_by_tag_category(category_name, tag_ids):
        return (db_session.query(Video)
                .join(Tag, Video.tags)
                .join(TagCategory)
                .filter(TagCategory.name == category_name)
                .filter(Tag.id.in_(tag_ids))
                .distinct()
                .all())

    @staticmethod
    def get_videos_by_presenters(presenter_ids):
        return (db_session.query(Video)
                .join(Video.presenters)
                .filter(Presenter.id.in_(presenter_ids))
                .distinct()
                .all())

    @staticmethod
    def get_videos_by_search_terms(search_terms, presenter_names, tag_names):
        return (db_session.query(Video)
                .outerjoin(Tag, Video.tags)
                .outerjoin(Video.presenters)
                .group_by(Video.id)
                .having(
                    or_(
                        func.lower(func.string_agg(Presenter.name, ' ')).contains(search_terms.lower()),
                        func.lower(func.string_agg(Tag.name, ' ')).contains(search_terms.lower()),
                        *[
                            or_(
                                func.lower(Video.title).contains(term),
                                func.lower(Video.description).contains(term)
                            ) for term in search_terms.split()
                        ]
                    )
                )
                .all()) 
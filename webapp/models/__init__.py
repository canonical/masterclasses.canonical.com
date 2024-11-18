from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Define association tables
video_presenters = Table(
    'video_presenters', Base.metadata,
    Column('video_id', Integer, ForeignKey('videos.id')),
    Column('presenter_id', Integer, ForeignKey('presenters.id'))
)

video_tags = Table(
    'video_tags', Base.metadata,
    Column('video_id', Integer, ForeignKey('videos.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

from .video import Video
from .presenter import Presenter
from .tag import Tag, TagCategory

# This ensures all models are loaded
__all__ = ['Video', 'Presenter', 'Tag', 'TagCategory', 'Base'] 
from sqlalchemy import Column, Integer, ForeignKey
from models.base import Base

class VideoPresenter(Base):
    __tablename__ = "video_presenters"

    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'), primary_key=True)
    presenter_id = Column(Integer, ForeignKey('presenters.id', ondelete='CASCADE'), primary_key=True)

class VideoTag(Base):
    __tablename__ = "video_tags"

    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tag.id', ondelete='CASCADE'), primary_key=True) 
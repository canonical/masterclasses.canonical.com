from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    unixstart = Column(Integer, nullable=False)
    unixend = Column(Integer, nullable=False)
    stream = Column(String, nullable=True)
    slides = Column(String, nullable=True)
    recording = Column(String, nullable=True)
    chat_log = Column(String, nullable=True)
    thumbnails = Column(String, nullable=True)
    calendar_event = Column(String, nullable=True)

    # Relationships
    presenters = relationship("Presenter", secondary="video_presenters", back_populates="videos")
    tags = relationship("Tag", secondary="video_tags", back_populates="videos") 
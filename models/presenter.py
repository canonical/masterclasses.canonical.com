from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from models.base import Base

class Presenter(Base):
    __tablename__ = "presenters"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    hrc_id = Column(Integer, nullable=True)
    headshot = Column(String, nullable=True)

    # Relationships
    videos = relationship("Video", secondary="video_presenters", back_populates="presenters") 
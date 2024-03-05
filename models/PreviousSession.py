from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.sql import func
from models.base import Base

class PreviousSession(Base):
  __tablename__ = "previous_sessions"

  id = Column(Integer, primary_key=True)
  topic = Column(String, nullable=False)
  owner = Column(String, nullable=False)
  duration = Column(String, nullable=False)
  date = Column(Date, nullable=False, default=func.now())
  slides = Column(String, nullable=True)
  recording = Column(String, nullable=True)
  description = Column(String, nullable=True)
  chat_log = Column(String, nullable=True)
  tags = Column(String, nullable=True)
  thumbnails = Column(String, nullable=False)

  def __repr__(self):
    return f"<PreviousSession(topic={self.topic}, owner={self.owner}, duration={self.duration}, date={self.date}, slides={self.slides}, recording={self.recording}, description={self.description}, chat_log={self.chat_log}, tags={self.tags}, thumbnails={self.thumbnails})>"

from sqlalchemy import Column, Date, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func

class Base(DeclarativeBase):
  pass


class PreviousSession(Base):
  __tablename__ = "previous_sessions"

  id = Column(Integer, primary_key=True)
  topic = Column(String, nullable=False)
  owner = Column(String, nullable=False)
  duration = Column(String, nullable=False)
  date = Column(Date, nullable=False, default=func.now())
  slides = Column(String, nullable=True)
  recording = Column(String, nullable=False)
  description = Column(String, nullable=True)
  chat_log = Column(String, nullable=True)
  tags = Column(String, nullable=True)
  thumbnails = Column(String, nullable=False)

  def __repr__(self):
    return f"<PreviousSession(topic={self.topic}, owner={self.owner}, duration={self.duration}, date={self.date}, slides={self.slides}, recording={self.recording}, description={self.description}, chat_log={self.chat_log}, tags={self.tags}, thumbnails={self.thumbnails})>"


class UpcomingSession(Base):
  __tablename__ = "upcoming_sessions"

  id = Column(Integer, primary_key=True)
  topic = Column(String, nullable=False)
  owner = Column(String, nullable=False)
  duration = Column(String, nullable=False)
  date = Column(Date, nullable=True, default=func.now())
  notes = Column(String, nullable=True)
  event = Column(String, nullable=True)

  def __repr__(self):
    return f"<UpcomingSession(topic={self.topic}, owner={self.owner}, duration={self.duration}, date={self.date}, notes={self.notes}, event={self.event})>"


class SprintSession(Base):
  __tablename__ = "sprint_session"

  id = Column(Integer, primary_key=True)
  topic = Column(String, nullable=False)
  owner = Column(String, nullable=False)
  duration = Column(String, nullable=False)
  date = Column(Date, nullable=False, default=func.now())
  slides = Column(String, nullable=True)
  recording = Column(String, nullable=False)
  description = Column(String, nullable=True)
  chat_log = Column(String, nullable=True)
  tags = Column(String, nullable=True)
  thumbnails = Column(String, nullable=False)

  def __repr__(self):
    return f"<SprintSession(topic={self.topic}, owner={self.owner}, duration={self.duration}, date={self.date}, slides={self.slides}, recording={self.recording}, description={self.description}, chat_log={self.chat_log}, tags={self.tags}, thumbnails={self.thumbnails})>"
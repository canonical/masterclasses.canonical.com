from sqlalchemy import Column, Date, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func

class Base(DeclarativeBase):
  pass


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
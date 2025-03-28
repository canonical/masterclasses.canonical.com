import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

# Create engine with proper connection pool settings
engine = create_engine(
    os.environ.get("DATABASE_URL"),
    pool_size=5,  # Default is 5
    max_overflow=10,  # Default is 10
    pool_timeout=30,  # Default is 30
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True  # Check connection validity before using it
)

# Create a session factory
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

# Helper function to remove session at the end of requests
def close_db_session(exception=None):
    db_session.remove()
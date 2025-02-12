import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

db_engine = create_engine(os.getenv("DATABASE_URL"))
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
)
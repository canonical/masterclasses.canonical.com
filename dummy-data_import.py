# import csv data into our demo database
import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text
from models.PreviousSession import PreviousSession
from models.UpcomingSession import UpcomingSession
from models.SprintSession import SprintSession

db_engine = create_engine(os.getenv("DATABASE_URL"))
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
)


def main():
    db_session.execute(text("TRUNCATE TABLE previous_sessions"))
    db_session.execute(text("TRUNCATE TABLE upcoming_sessions"))
    db_session.execute(text("TRUNCATE TABLE sprint_sessions"))

    print("Inserting dummy data into the database...")
    db_session.bulk_insert_mappings(
        PreviousSession,
        [
            {
                "id": 1,
                "topic": "Python",
                "owner": "John Doe",
                "duration": "1 hour",
                "date": "2024-03-06",
                "slides": "https://slides.com",
                "recording": "https://recording.com",
                "description": "Python session",
                "chat_log": "https://chat.com",
                "tags": "python",
                "thumbnails": "https://http.cat/200",
            },
            {
                "id": 2,
                "topic": "Django",
                "owner": "Jane Doe",
                "duration": "1 hour",
                "date": "2024-03-06",
                "slides": "https://slides.com",
                "recording": "https://recording.com",
                "description": "Django session",
                "chat_log": "https://chat.com",
                "tags": "django",
                "thumbnails": "https://http.cat/200",
            },
        ],
    )
    db_session.bulk_insert_mappings(
        UpcomingSession,
        [
            {
                "id": 1,
                "topic": "Flamenco",
                "owner": "Jane Doe",
                "duration": "1 hour",
                "date": "2024-03-06",
                "notes": "Flamenco session",
                "event": "https://event.com",
            },
            {
                "id": 2,
                "topic": "Tabla",
                "owner": "Jane Doe",
                "duration": "1 hour",
                "date": "2024-03-06",
                "notes": "Tabla session",
                "event": "https://event.com",
            },
        ],
    )
    db_session.bulk_insert_mappings(
        SprintSession,
        [
            {
                "id": 1,
                "topic": "Opening Plenary",
                "owner": "Mark",
                "duration": "1 hour",
                "date": "2024-03-06",
                "slides": "https://slides.com",
                "recording": "https://recording.com",
                "description": "Python session",
                "chat_log": "https://chat.com",
                "tags": "tag1,tag2",
                "thumbnails": "https://http.cat/200",
            },
            {
                "id": 2,
                "topic": "Closing Plenary",
                "owner": "Mark",
                "duration": "1 hour",
                "date": "2024-03-06",
                "slides": "https://slides.com",
                "recording": "https://recording.com",
                "description": "Django session",
                "chat_log": "https://chat.com",
                "tags": "tag3,tag4",
                "thumbnails": "https://http.cat/200",
            },
        ],
    )
    db_session.commit()
    print("Dummy data inserted successfully")


if __name__ == "__main__":
    # Only run this script if in demo environment
    if os.getenv("OPENID_LAUNCHPAD_TEAM") == "canonical-content-people":
        main()

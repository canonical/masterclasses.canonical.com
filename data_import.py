# import csv data into our production database
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


def import_data(file_name, model_class):
    """
    Imports data from a CSV file into a database table using a provided model class.

    Args:
        file_name (str): Path to the CSV file containing the data to import.
        model_class (class): The SQLAlchemy model class representing the database table.
    """
    with open(file_name, "r") as file:
        rows = csv.DictReader(file)
        for row in rows:
            session_obj = model_class(**row)
            db_session.add(session_obj)
        db_session.commit()


def confirm_truncate(tables):
    """
    Prompts user for confirmation before truncating tables.
    Args:
        tables: List of table names to be truncated.
    Returns:
        bool: True if user confirms truncation, False otherwise.
    """
    message = "Are you sure you want to truncate the following tables?\n"
    for table in tables:
        message += f"- {table}\n"
    message += "This will delete all existing data in these tables.\n"
    response = input(message + "(y/N): ")
    return response.lower() == "y"


def main():
    tables = ["previous_sessions", "upcoming_sessions", "sprint_sessions"]
    if confirm_truncate(tables):
        print("Truncating tables...")
        for table in tables:
            db_session.execute(text(f"TRUNCATE TABLE {table}"))
        db_session.commit()
        print("Tables truncated.")
        print("Importing data into the database...")
        import_data("previous_sessions.csv", PreviousSession)
        import_data("upcoming_sessions.csv", UpcomingSession)
        import_data("sprint_sessions.csv", SprintSession)
        print("Data imported successfully.")
    else:
        print("Truncation cancelled. Data import aborted.")


if __name__ == "__main__":
    main()

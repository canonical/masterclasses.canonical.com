import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from webapp.app import app
from models.base import Base


@pytest.fixture
def test_app():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def test_db():
    # Use SQLite for testing
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(bind=engine)
    test_db = TestingSessionLocal()

    yield test_db

    Base.metadata.drop_all(engine)
    test_db.close()

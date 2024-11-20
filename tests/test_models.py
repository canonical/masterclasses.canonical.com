import pytest
from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from datetime import datetime, timezone

def test_video_creation(test_db):
    video = Video(
        title="Test Video",
        description="Test Description",
        unixstart=int(datetime.now(timezone.utc).timestamp()),
        unixend=int(datetime.now(timezone.utc).timestamp()) + 3600,
        stream="https://example.com/stream",
    )
    test_db.add(video)
    test_db.commit()
    
    assert video.id is not None
    assert video.title == "Test Video"

def test_video_presenter_relationship(test_db):
    video = Video(
        title="Test Video",
        unixstart=int(datetime.now(timezone.utc).timestamp()),
        unixend=int(datetime.now(timezone.utc).timestamp()) + 3600,
    )
    presenter = Presenter(
        name="Test Presenter",
        email="test@canonical.com",
        hrc_id="123"
    )
    
    video.presenters.append(presenter)
    test_db.add(video)
    test_db.commit()
    
    assert len(video.presenters) == 1
    assert video.presenters[0].name == "Test Presenter" 
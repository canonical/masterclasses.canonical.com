# import csv data into our demo database
import csv
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime
import time

from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from models.associations import VideoPresenter, VideoTag

db_engine = create_engine(os.getenv("DATABASE_URL"))
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
)


def main():
    # Clear all existing data
    db_session.execute(text("TRUNCATE TABLE video_tags CASCADE"))
    db_session.execute(text("TRUNCATE TABLE video_presenters CASCADE"))
    db_session.execute(text("TRUNCATE TABLE videos CASCADE"))
    db_session.execute(text("TRUNCATE TABLE presenters CASCADE"))
    db_session.execute(text("TRUNCATE TABLE tag CASCADE"))
    db_session.execute(text("TRUNCATE TABLE tag_category CASCADE"))
    
    print("Inserting dummy data into the database...")
    
    # Create tag categories
    topic_category = TagCategory(name="Topic")
    event_category = TagCategory(name="Event")
    date_category = TagCategory(name="Date")
    db_session.add_all([topic_category, event_category, date_category])
    db_session.flush()  # This ensures we have IDs for the categories
    
    # Create tags
    tags = {
        "Web": Tag(name="Web", tag_type_id=topic_category.id),
        "Leadership": Tag(name="Leadership", tag_type_id=topic_category.id),
        "Databases": Tag(name="Databases", tag_type_id=topic_category.id),
        "Masterclass": Tag(name="Masterclass", tag_type_id=event_category.id),
        "Town Hall": Tag(name="Town Hall", tag_type_id=event_category.id),
        "Engineering Sprint": Tag(name="Engineering Sprint", tag_type_id=event_category.id),
        "Roadmap Sprint": Tag(name="Roadmap Sprint", tag_type_id=event_category.id),
        "Commercial Sprint": Tag(name="Commercial Sprint", tag_type_id=event_category.id),
        "Q4 2024": Tag(name="Q4 2024", tag_type_id=date_category.id),
        "Q3 2024": Tag(name="Q3 2024", tag_type_id=date_category.id),
        "Q2 2024": Tag(name="Q2 2024", tag_type_id=date_category.id),
        "Q1 2024": Tag(name="Q1 2024", tag_type_id=date_category.id),
    }
    db_session.add_all(tags.values())
    
    # Create presenters
    presenters = {
        "Finn": Presenter(
            name="Finn Rawles Malliagh",
            email="finn.rawles@canonical.com",
            hrc_id=1,
            headshot="https://www.gravatar.com/avatar/123"
        ),
        "Melissa": Presenter(
            name="Melissa Carlson",
            email="melissa.carlson@canonical.com",
            hrc_id=2,
            headshot="https://www.gravatar.com/avatar/456"
        ),
        "Robby": Presenter(
            name="Robby Pocase",
            email="robby.pocase@canonical.com",
            hrc_id=3,
            headshot="https://www.gravatar.com/avatar/789"
        )
    }
    db_session.add_all(presenters.values())
    db_session.flush()  # This ensures we have IDs for the presenters
    
    # Create videos
    videos = [
        Video(
            title="Open source and its social impact",
            description="This is a very long description. Lorem ipsum dolor sit amet consectetur adipisicing elit. Qui dolor minima officia voluptates ipsa dignissimos ex ab in commodi accusantium dicta facere alias aliquid, corporis, perferendis sit possimus necessitatibus excepturi?",
            unixstart=int(time.mktime(datetime(2024, 3, 6, 14, 0).timetuple())),
            unixend=int(time.mktime(datetime(2024, 3, 6, 15, 0).timetuple())),
            slides="https://docs.google.com/presentation/d/1SwnD-BDTBUO92Y8mPYxc_Ab2_a2-T0S0urdBCJpu0A8/edit?usp=sharing",
            recording="https://drive.google.com/file/d/19h7daA-TDB_s5jjQkOka9Hv2Ei7ivOhJ/view?usp=sharing",
            chat_log="https://chat.com",
            thumbnails="https://assets.ubuntu.com/v1/1dc989d8-Emails%20for%20human%20beings.png",
            calendar_event="https://calendar.google.com/calendar/u/0/event?eid=N2VuNGFqaWo0MHZmMHVybnQzNWI1ZTVmNnMgY19pdnJiaGtjdGl0a2RuY3IxMGV2Mmo4bWEya0Bn"
        ),
        Video(
            title="Django Web Development",
            description="Django session covering web development basics",
            unixstart=int(time.mktime(datetime(2024, 3, 7, 14, 0).timetuple())),
            unixend=int(time.mktime(datetime(2024, 3, 7, 15, 0).timetuple())),
            slides="https://docs.google.com/presentation/d/1SwnD-BDTBUO92Y8mPYxc_Ab2_a2-T0S0urdBCJpu0A8/edit?usp=sharing",
            recording="https://drive.google.com/file/d/13jPWqLIEg-V2lmW7qF4TtX6TjIz6k-8C/view?usp=sharing",
            thumbnails="https://masterclasses.canonical.com/social-styles-class-1027",
            calendar_event="https://calendar.google.com/calendar/u/0/event?eid=N2VuNGFqaWo0MHZmMHVybnQzNWI1ZTVmNnMgY19pdnJiaGtjdGl0a2RuY3IxMGV2Mmo4bWEya0Bn"
        ),
        Video(
            title="A video way in the future",
            description="This is a talk that will happen in the future, there isn't any content here yet.",
            unixstart=int(time.mktime(datetime(2025, 3, 7, 14, 0).timetuple())),
            unixend=int(time.mktime(datetime(2025, 3, 7, 15, 0).timetuple())),
            slides="https://docs.google.com/presentation/d/1SwnD-BDTBUO92Y8mPYxc_Ab2_a2-T0S0urdBCJpu0A8/edit?usp=sharing",
            thumbnails="https://masterclasses.canonical.com/social-styles-class-1027",
            calendar_event="https://calendar.google.com/calendar/u/0/event?eid=N2VuNGFqaWo0MHZmMHVybnQzNWI1ZTVmNnMgY19pdnJiaGtjdGl0a2RuY3IxMGV2Mmo4bWEya0Bn"
        ),
        Video(
            title="A livestream that is currently happening",
            description="This is a talk that is currently happening, woo!",
            unixstart=int(time.mktime(datetime(2023, 3, 7, 14, 0).timetuple())),
            unixend=int(time.mktime(datetime(2026, 3, 7, 15, 0).timetuple())),
            stream="https://stream.meet.google.com/stream/f0e34307-f3e1-43aa-b456-56f4f45c514c?authuser=0",
            slides="https://docs.google.com/presentation/d/1SwnD-BDTBUO92Y8mPYxc_Ab2_a2-T0S0urdBCJpu0A8/edit?usp=sharing",
            thumbnails="https://masterclasses.canonical.com/social-styles-class-1027",
            calendar_event="https://calendar.google.com/calendar/u/0/event?eid=N2VuNGFqaWo0MHZmMHVybnQzNWI1ZTVmNnMgY19pdnJiaGtjdGl0a2RuY3IxMGV2Mmo4bWEya0Bn"
        ),
        Video(
            title="A livestream that is happening in less than 24 hours ",
            description="This is a talk that is happening in less than 24 hours, woo!",
            unixstart=int(time.mktime(datetime(2024, 11, 16, 7, 0).timetuple())),
            unixend=int(time.mktime(datetime(2024, 11, 17, 7, 0).timetuple())),
            stream="https://stream.meet.google.com/stream/f0e34307-f3e1-43aa-b456-56f4f45c514c?authuser=0",
            slides="https://docs.google.com/presentation/d/1SwnD-BDTBUO92Y8mPYxc_Ab2_a2-T0S0urdBCJpu0A8/edit?usp=sharing",
            thumbnails="https://masterclasses.canonical.com/social-styles-class-1027",
            calendar_event="https://calendar.google.com/calendar/u/0/event?eid=N2VuNGFqaWo0MHZmMHVybnQzNWI1ZTVmNnMgY19pdnJiaGtjdGl0a2RuY3IxMGV2Mmo4bWEya0Bn"
        )
    ]
    db_session.add_all(videos)
    db_session.flush()

    # Associate videos with presenters
    video_presenters = [
        VideoPresenter(video_id=videos[0].id, presenter_id=presenters["Finn"].id),
        VideoPresenter(video_id=videos[0].id, presenter_id=presenters["Robby"].id),
        VideoPresenter(video_id=videos[1].id, presenter_id=presenters["Melissa"].id),
        VideoPresenter(video_id=videos[2].id, presenter_id=presenters["Finn"].id),
        VideoPresenter(video_id=videos[3].id, presenter_id=presenters["Melissa"].id),
        VideoPresenter(video_id=videos[3].id, presenter_id=presenters["Robby"].id),
        VideoPresenter(video_id=videos[3].id, presenter_id=presenters["Finn"].id),
        VideoPresenter(video_id=videos[4].id, presenter_id=presenters["Melissa"].id),
    ]
    db_session.add_all(video_presenters)
    db_session.flush()

    # Associate videos with tags
    video_tags = [
        VideoTag(video_id=videos[0].id, tag_id=tags["Web"].id),
        VideoTag(video_id=videos[0].id, tag_id=tags["Leadership"].id),
        VideoTag(video_id=videos[0].id, tag_id=tags["Masterclass"].id),
        VideoTag(video_id=videos[0].id, tag_id=tags["Q4 2024"].id),
        VideoTag(video_id=videos[1].id, tag_id=tags["Databases"].id),
        VideoTag(video_id=videos[1].id, tag_id=tags["Town Hall"].id),
        VideoTag(video_id=videos[1].id, tag_id=tags["Q3 2024"].id),
        VideoTag(video_id=videos[2].id, tag_id=tags["Engineering Sprint"].id),
        VideoTag(video_id=videos[3].id, tag_id=tags["Commercial Sprint"].id),
        VideoTag(video_id=videos[4].id, tag_id=tags["Town Hall"].id),
        VideoTag(video_id=videos[4].id, tag_id=tags["Q2 2024"].id),
    ]
    db_session.add_all(video_tags)
    db_session.flush()

    db_session.commit()
    print("Dummy data inserted successfully")


if __name__ == "__main__":
    # Only run this script if in demo environment
    if os.getenv("OPENID_LAUNCHPAD_TEAM") == "canonical-content-people":
        main()

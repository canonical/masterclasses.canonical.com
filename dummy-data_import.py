# import csv data into our demo database
import csv
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime, timedelta, timezone
import time
import random

from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from models.associations import VideoPresenter, VideoTag

db_engine = create_engine(os.getenv("DATABASE_URL"))
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
)


def generate_random_title(min_words=2, max_words=10):
    words = ['Advanced', 'Introduction', 'Deep Dive', 'Workshop', 'Tutorial', 'Guide', 
             'Mastering', 'Exploring', 'Understanding', 'Building', 'Deploying', 'Scaling',
             'Managing', 'Securing', 'Optimizing', 'Debugging', 'Testing', 'Monitoring',
             'Python', 'Django', 'Flask', 'Database', 'Cloud', 'DevOps', 'Security',
             'Performance', 'Architecture', 'Design', 'Infrastructure', 'Kubernetes',
             'Docker', 'CI/CD', 'APIs', 'Microservices', 'Web', 'Mobile', 'Analytics']
    
    num_words = random.randint(min_words, max_words)
    return ' '.join(random.sample(words, num_words))

def generate_random_description(max_words=100):
    words = ['Lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 
             'elit', 'sed', 'do', 'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 
             'et', 'dolore', 'magna', 'aliqua', 'Ut', 'enim', 'ad', 'minim', 'veniam',
             'quis', 'nostrud', 'exercitation', 'ullamco', 'laboris', 'nisi', 'ut',
             'aliquip', 'ex', 'ea', 'commodo', 'consequat']
    
    num_words = random.randint(0, max_words)
    return ' '.join(random.choices(words, k=num_words)) if num_words > 0 else None

def generate_random_duration():
    # Generate duration between 5 minutes and 3 hours in 5-minute increments
    min_minutes = 5
    max_minutes = 180  # 3 hours
    duration_minutes = random.randrange(min_minutes, max_minutes + 1, 5)
    return duration_minutes

def generate_random_thumbnail():
    thumbnails = [
        "https://assets.ubuntu.com/v1/1dc989d8-Emails%20for%20human%20beings.png",
        "https://assets.ubuntu.com/v1/39ed4a41-Stephanie%20Domas.png",
        "https://assets.ubuntu.com/v1/bd381e83-Masterclasses%20Thumbnail%20Template%202023%20(11).jpg",
        "https://assets.ubuntu.com/v1/49a20966-Masterclasses%20Thumbnail%20Template%202023%20(1).png",
        "https://assets.ubuntu.com/v1/715963b6-Masterclasses%20Thumbnail%20Template%202023%20(10).jpg",
        "https://assets.ubuntu.com/v1/18bd0ee7-Masterclasses%20Thumbnail%20Template%202023%20(23).jpg",
        "https://assets.ubuntu.com/v1/0adbedcb-Masterclasses%20Thumbnail%20Template%202023%20(5).jpg",
    ]
    return random.choice(thumbnails)

def main():
    # Clear all existing data
    db_session.execute(text("TRUNCATE TABLE video_tags CASCADE"))
    db_session.execute(text("TRUNCATE TABLE video_presenters CASCADE"))
    db_session.execute(text("TRUNCATE TABLE videos CASCADE"))
    db_session.execute(text("TRUNCATE TABLE presenters CASCADE"))
    db_session.execute(text("TRUNCATE TABLE tag CASCADE"))
    db_session.execute(text("TRUNCATE TABLE tag_category CASCADE"))
    
    # Create tag categories
    topic_category = TagCategory(name="Topic")
    event_category = TagCategory(name="Event")
    date_category = TagCategory(name="Date")
    db_session.add_all([topic_category, event_category, date_category])
    db_session.flush()
    
    # Create tags with more variety
    tags = {
        # Topics
        "Web": Tag(name="Web", tag_type_id=topic_category.id),
        "Leadership": Tag(name="Leadership", tag_type_id=topic_category.id),
        "Databases": Tag(name="Databases", tag_type_id=topic_category.id),
        "Python": Tag(name="Python", tag_type_id=topic_category.id),
        "DevOps": Tag(name="DevOps", tag_type_id=topic_category.id),
        "Security": Tag(name="Security", tag_type_id=topic_category.id),
        
        # Events
        "Masterclass": Tag(name="Masterclass", tag_type_id=event_category.id),
        "Town Hall": Tag(name="Town Hall", tag_type_id=event_category.id),
        "Engineering Sprint": Tag(name="Engineering Sprint", tag_type_id=event_category.id),
        "Roadmap Sprint": Tag(name="Roadmap Sprint", tag_type_id=event_category.id),
        "Commercial Sprint": Tag(name="Commercial Sprint", tag_type_id=event_category.id),
        "Workshop": Tag(name="Workshop", tag_type_id=event_category.id),
        
        # Dates
        "Q4 2024": Tag(name="Q4 2024", tag_type_id=date_category.id),
        "Q3 2024": Tag(name="Q3 2024", tag_type_id=date_category.id),
        "Q2 2024": Tag(name="Q2 2024", tag_type_id=date_category.id),
        "Q1 2024": Tag(name="Q1 2024", tag_type_id=date_category.id),
    }
    db_session.add_all(tags.values())
    
    # Create more presenters
    presenters = {
        "Finn": Presenter(name="Finn Rawles", email="finn.rawles@canonical.com", hrc_id=1),
        "Melissa": Presenter(name="Melissa Carlson", email="melissa.carlson@canonical.com", hrc_id=2),
        "Robby": Presenter(name="Robby Pocase", email="robby.pocase@canonical.com", hrc_id=3),
        "Sarah": Presenter(name="Sarah Smith", email="sarah.smith@canonical.com", hrc_id=4),
        "James": Presenter(name="James Wilson", email="james.wilson@canonical.com", hrc_id=5),
        "Emma": Presenter(name="Emma Brown", email="emma.brown@canonical.com", hrc_id=6),
    }
    db_session.add_all(presenters.values())
    db_session.flush()
    
    # Create videos with specific timing for upcoming events
    now = datetime.now(timezone.utc)
    videos = []
    
    # Helper function to create video with random title and description
    def create_video(start_time, end_time, has_recording=True):
        return Video(
            title=generate_random_title(),
            description=generate_random_description(),
            unixstart=int(start_time.timestamp()),
            unixend=int(end_time.timestamp()),
            recording=f"https://drive.google.com/file/d/1IgzCDxDOJp3rQBNuSxNddkhwz88i3yoU/view?usp=drive_link" if has_recording else None,
            stream=f"https://example.com/stream_{len(videos)}",
            calendar_event=f"https://calendar.google.com/calendar/u/0/event?eid=MmtiNmVjanA0NzJwYThzY2VnczgyazlzbjcgY183MTgyOTllYjQzZTg4YTg4YmFhMWY3ZDJjNjA5ZTcwMDQ2NzA4OGE4MzRkZWE4ZjJlYTQyZjA1Mjc1NDhiMzgwQGc",
            slides=f"https://example.com/slides_{len(videos)}",
            thumbnails=generate_random_thumbnail()
        )

    # Create past videos (with recordings)
    for i in range(30):
        past_start = now - timedelta(days=i+1, hours=random.randint(1, 8))
        duration = timedelta(minutes=generate_random_duration())
        videos.append(create_video(past_start, past_start + duration))

    # Create currently live event (4 hours duration)
    live_start = now - timedelta(hours=2)  # Started 2 hours ago
    live_end = live_start + timedelta(hours=4)  # Will end in 2 hours
    videos.append(create_video(live_start, live_end, has_recording=False))

    # Create event starting in 10 hours
    next_start = now + timedelta(hours=10)
    duration = timedelta(minutes=generate_random_duration())
    videos.append(create_video(next_start, next_start + duration, has_recording=False))

    # Create event starting in 4 days
    future_start = now + timedelta(days=4)
    duration = timedelta(minutes=generate_random_duration())
    videos.append(create_video(future_start, future_start + duration, has_recording=False))

    db_session.add_all(videos)
    db_session.flush()

    # Create varied combinations of video-presenter associations
    video_presenters = [
        # Video 1: Single presenter
        VideoPresenter(video_id=videos[0].id, presenter_id=presenters["Finn"].id),
        
        # Video 2: Two presenters
        VideoPresenter(video_id=videos[1].id, presenter_id=presenters["Melissa"].id),
        VideoPresenter(video_id=videos[1].id, presenter_id=presenters["Robby"].id),
        
        # Video 3: Three presenters
        VideoPresenter(video_id=videos[2].id, presenter_id=presenters["Sarah"].id),
        VideoPresenter(video_id=videos[2].id, presenter_id=presenters["James"].id),
        VideoPresenter(video_id=videos[2].id, presenter_id=presenters["Emma"].id),
        
        # Video 4: Overlapping presenters
        VideoPresenter(video_id=videos[3].id, presenter_id=presenters["Finn"].id),
        VideoPresenter(video_id=videos[3].id, presenter_id=presenters["Sarah"].id),
        
        # Additional varied combinations...
        VideoPresenter(video_id=videos[4].id, presenter_id=presenters["Emma"].id),
        VideoPresenter(video_id=videos[4].id, presenter_id=presenters["Melissa"].id),
        VideoPresenter(video_id=videos[5].id, presenter_id=presenters["Robby"].id),
        VideoPresenter(video_id=videos[6].id, presenter_id=presenters["James"].id),
        VideoPresenter(video_id=videos[7].id, presenter_id=presenters["Finn"].id),
        VideoPresenter(video_id=videos[7].id, presenter_id=presenters["Emma"].id),
        VideoPresenter(video_id=videos[8].id, presenter_id=presenters["Sarah"].id),
        VideoPresenter(video_id=videos[9].id, presenter_id=presenters["Melissa"].id),
    ]

    # Create random video-presenter associations for the rest of the videos
    for i in range(10, len(videos)):
        num_presenters = random.randint(1, 5)
        presenter_list = list(presenters.values())  # Convert dict_values to list
        selected_presenters = random.sample(presenter_list, min(num_presenters, len(presenter_list)))
        for presenter in selected_presenters:
            video_presenters.append(VideoPresenter(video_id=videos[i].id, presenter_id=presenter.id))

    db_session.add_all(video_presenters)
    
    # Create varied combinations of video tags with multiple topics possible
    video_tags = []
    
    # Define tag combinations for each video
    video_tag_data = [
        (0, ["Web", "Security"], "Masterclass", "Q1 2024"),
        (1, ["Databases", "Python", "DevOps"], "Workshop", "Q1 2024"),
        (2, ["Security", "Leadership"], "Town Hall", "Q2 2024"),
        (3, ["Web", "Leadership", "Python"], "Engineering Sprint", "Q2 2024"),
        (4, ["Databases", "DevOps"], "Commercial Sprint", "Q3 2024"),
        (5, ["Python", "Security"], "Roadmap Sprint", "Q3 2024"),
        (6, ["DevOps", "Web"], "Masterclass", "Q4 2024"),
        (7, ["Security", "Databases"], "Workshop", "Q4 2024"),
        (8, ["Web", "Python"], "Town Hall", "Q4 2024"),
        (9, ["Leadership", "DevOps", "Security"], "Engineering Sprint", "Q4 2024")
    ]

    # generate random video-tag associations for the rest of the videos
    for i in range(10, len(videos)):
        # Convert tags.values() to list once
        tag_list = list(tags.values())
        # Select random number of unique tags
        num_tags = random.randint(1, 5)
        selected_tags = random.sample(tag_list, min(num_tags, len(tag_list)))
        for tag in selected_tags:
            video_tags.append(VideoTag(video_id=videos[i].id, tag_id=tag.id))

    # Create video tags
    for video_index, topic_list, event, date in video_tag_data:
        # Add topic tags
        for topic in topic_list:
            video_tags.append(VideoTag(video_id=videos[video_index].id, tag_id=tags[topic].id))
        # Add event and date tags
        video_tags.append(VideoTag(video_id=videos[video_index].id, tag_id=tags[event].id))
        video_tags.append(VideoTag(video_id=videos[video_index].id, tag_id=tags[date].id))

    db_session.add_all(video_tags)
    db_session.commit()


if __name__ == "__main__":
    # Only run this script if in demo environment
    if os.getenv("OPENID_LAUNCHPAD_TEAM") == "canonical-content-people":
        main()

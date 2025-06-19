# Import static placeholder data from JSON files
import json
import os
import sys
from pathlib import Path
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime, timezone

# Add project root to path so we can import models
sys.path.append(str(Path(__file__).parent.parent))

from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from models.associations import VideoPresenter, VideoTag

# Setup database connection
db_engine = create_engine(os.getenv("DATABASE_URL"))
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
)

# Add color constants at the top of the file
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
END = "\033[0m"

def load_json_file(filename):
    """Load JSON data from a file in the placeholderdata-output directory."""
    file_path = Path(__file__).parent / 'placeholderdata-output' / filename
    with open(file_path, 'r') as f:
        return json.load(f)

def get_required_field(data_dict, field_name):
    """Get a required field or throw a descriptive error."""
    if field_name not in data_dict:
        raise KeyError(f"Missing required field '{field_name}' in data: {data_dict}")
    return data_dict[field_name]

def convert_datetime_to_unix(datetime_str):
    """Convert a datetime string (YYYY-MM-DD HH:MM) to a Unix timestamp."""
    if not datetime_str:
        return None
    try:
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        # Assume UTC timezone if not specified
        dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except ValueError as e:
        print(f"Error parsing datetime: {datetime_str} - {e}")
        return None

def check_required_files():
    """
    Check if all required JSON files exist in the placeholderdata-output directory.
    Returns tuple of (bool, str) indicating success and any error message.
    """
    required_files = [
        ('presenters.json', 'Presenters'),
        ('videos.json', 'Videos'),
        ('tags.json', 'Tags'),
        ('tag_categories.json', 'Tag Categories')
    ]
    
    missing_files = []
    for filename, description in required_files:
        if not (Path(__file__).parent / 'placeholderdata-output' / filename).exists():
            missing_files.append(filename)
    
    if missing_files:
        error_msg = (
            f"\n{RED}{BOLD}Error:{END} Missing required files in {UNDERLINE}scripts/placeholderdata-output/{END}: "
            f"{RED}{', '.join(missing_files)}{END}\n\n"
            f"{BOLD}Required steps:{END}\n\n"
            f"1. Export the data from {BLUE}https://masterclasses.canonical.com/admin/video{END}:\n"
            "   - Export Videos\n"
            "   - Export Presenters\n"
            "   - Export Tags\n"
            "   - Export Tag Categories\n\n"
            f"{BOLD}Then EITHER:{END}\n\n"
            f"Option 1: Use the exported files directly\n"
            f"   - Place the exported JSON files in {UNDERLINE}scripts/placeholderdata-output/{END}\n\n"
            f"{BOLD}OR{END}\n\n"
            f"Option 2: Anonymize the data first\n"
            f"   - Place the exported JSON files in {UNDERLINE}scripts/placeholderdata-input/{END}\n"
            f"   - Run: {GREEN}python3 scripts/anonymize-static-data.py{END}\n"
            f"   - The anonymized files will be automatically created in {UNDERLINE}scripts/placeholderdata-output/{END}\n\n"
            "Then try running dotrun again.\n"
        )
        return False, error_msg
    
    return True, ""

def main():
    # Only run if in demo environment
    if os.getenv("OPENID_LAUNCHPAD_TEAM") != "canonical-content-people":
        print("Not in demo environment, skipping placeholder data import")
        return

    # Check if we have all required files
    files_ok, error_msg = check_required_files()
    if not files_ok:
        print(error_msg)
        sys.exit(1)

    print("Importing static placeholder data from JSON files...")
    
    try:
        # Clear all existing data
        db_session.execute(text("TRUNCATE TABLE video_tags CASCADE"))
        db_session.execute(text("TRUNCATE TABLE video_presenters CASCADE"))
        db_session.execute(text("TRUNCATE TABLE videos CASCADE"))
        db_session.execute(text("TRUNCATE TABLE presenters CASCADE"))
        db_session.execute(text("TRUNCATE TABLE tag CASCADE"))
        db_session.execute(text("TRUNCATE TABLE tag_category CASCADE"))
        
        # Load data from JSON files
        tag_categories_data = load_json_file('tag_categories.json')
        tags_data = load_json_file('tags.json')
        presenters_data = load_json_file('presenters.json')
        videos_data = load_json_file('videos.json')
        
        # Import tag categories
        tag_categories = {}
        for tc_data in tag_categories_data:
            tc = TagCategory(name=tc_data['name'])
            db_session.add(tc)
            db_session.flush()
            tag_categories[tc_data['name']] = tc
        
        # Import tags
        tags = {}
        for tag_data in tags_data:
            category_name = tag_data['category']
            tag = Tag(
                name=tag_data['name'],
                tag_type_id=tag_categories[category_name].id
            )
            db_session.add(tag)
            db_session.flush()
            tags[tag_data['name']] = tag
        
        # Import presenters
        presenters = {}
        for presenter_data in presenters_data:
            presenter = Presenter(
                name=presenter_data['name'],
                email=presenter_data.get('email', f"{presenter_data['name'].lower().replace(' ', '.')}@canonical.com"),
                hrc_id=presenter_data.get('hrc_id', None),
                headshot=presenter_data.get('headshot', None)
            )
            db_session.add(presenter)
            db_session.flush()
            presenters[presenter_data['name']] = presenter
        
        # Import videos
        videos = []
        for video_data in videos_data:
            try:
                # Check if we have start_time/end_time instead of unixstart/unixend
                if 'start_time' in video_data and 'unixstart' not in video_data:
                    video_data['unixstart'] = convert_datetime_to_unix(video_data['start_time'])
                if 'end_time' in video_data and 'unixend' not in video_data:
                    video_data['unixend'] = convert_datetime_to_unix(video_data['end_time'])
                
                # Get required fields with error handling
                title = get_required_field(video_data, 'title')
                unixstart = get_required_field(video_data, 'unixstart')
                unixend = get_required_field(video_data, 'unixend')
                
                video = Video(
                    title=title,
                    description=video_data.get('description', ''),  # Default to empty string
                    unixstart=unixstart,
                    unixend=unixend,
                    recording=video_data.get('recording'),
                    stream=video_data.get('stream'),
                    calendar_event=video_data.get('calendar_event'),
                    slides=video_data.get('slides'),
                    thumbnails=video_data.get('thumbnails')
                )
                db_session.add(video)
                db_session.flush()
                
                # Add presenters
                if 'presenters' in video_data:
                    for presenter_name in video_data['presenters']:
                        if presenter_name in presenters:
                            db_session.add(VideoPresenter(
                                video_id=video.id,
                                presenter_id=presenters[presenter_name].id
                            ))
                
                # Add tags
                if 'tags' in video_data:
                    for tag_item in video_data['tags']:
                        # Handle both string tags and object tags
                        if isinstance(tag_item, str):
                            tag_name = tag_item
                        elif isinstance(tag_item, dict) and 'name' in tag_item:
                            tag_name = tag_item['name']
                        else:
                            print(f"Skipping invalid tag format: {tag_item}")
                            continue
                            
                        if tag_name in tags:
                            db_session.add(VideoTag(
                                video_id=video.id,
                                tag_id=tags[tag_name].id
                            ))
                        else:
                            print(f"Warning: Tag '{tag_name}' not found in tags dictionary")
            except KeyError as e:
                # Log the specific error for each video entry
                print(f"Error processing video: {e}")
                continue  # Skip this video and continue with the next
        
        # Commit all changes
        db_session.commit()
        print("Static placeholder data import completed successfully")
        
    except Exception as e:
        db_session.rollback()
        print(f"Error importing static placeholder data: {e}")

if __name__ == "__main__":
    main() 
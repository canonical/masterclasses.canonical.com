#!/usr/bin/env python3
"""
Script to anonymize the presenter data and update references in videos.
- Replace hrc_id values with unique placeholders
- Replaces last names with randomly generated ones
- Updates emails to match new names
- Replaces headshot URLs with random portraits from randomuser.me
- Updates presenter references in videos.json

Reads from placeholderdata-input and writes to placeholderdata-output
"""

import json
import random
import unicodedata
import re
import os
import uuid
from urllib.request import urlopen
from urllib.error import URLError

# File paths
INPUT_DIR = "placeholderdata-input"
OUTPUT_DIR = "placeholderdata-output"

PRESENTERS_INPUT = f"{INPUT_DIR}/presenters.json"
VIDEOS_INPUT = f"{INPUT_DIR}/videos.json"
TAGS_INPUT = f"{INPUT_DIR}/tags.json"
TAG_CATEGORIES_INPUT = f"{INPUT_DIR}/tag_categories.json"

PRESENTERS_OUTPUT = f"{OUTPUT_DIR}/presenters.json"
VIDEOS_OUTPUT = f"{OUTPUT_DIR}/videos.json"
TAGS_OUTPUT = f"{OUTPUT_DIR}/tags.json"
TAG_CATEGORIES_OUTPUT = f"{OUTPUT_DIR}/tag_categories.json"

def get_random_portraits(count):
    """Fetch random portrait URLs from randomuser.me API."""
    try:
        with urlopen(f"https://randomuser.me/api/?results={count}") as response:
            data = json.loads(response.read())
            return [result['picture']['large'] for result in data['results']]
    except (URLError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to fetch random portraits: {e}")
        # Fallback to a set of default portrait URLs if the API call fails
        return [f"https://randomuser.me/api/portraits/{'women' if i%2 else 'men'}/{i}.jpg" 
                for i in range(count)]

# Sample surnames (some with diacritics, some compound)
SURNAMES = [
    "Smith", "Johnson", "Brown", "García", "Rodríguez", "Müller", "Jørgensen", 
    "López", "González", "Hernández", "Martínez", "Sánchez", "Pérez", "Martín",
    "Gómez", "Díaz", "Álvarez", "Ruiz", "Fernández", "Bjørn", "Guðmundsson", 
    "Kowalski", "Nowak", "Wójcik", "Kowalczyk", "Kamiński", "Zieliński", "Szymański",
    "Wang", "Li", "Zhang", "Chen", "Liu", "Yang", "Huang", "Kim", "Lee", "Suzuki",
    "Satō", "Takahashi", "Tanaka", "Watanabe", "Andersen", "Christensen", "Nielsen",
    "Jensen", "Hansen", "Larsen", "Sørensen", "Nguyen", "Trần", "Phạm", "Hoàng",
    "Bakker", "De Jong", "Jansen", "De Vries", "Van den Berg", "Van der Meer", "Ødegård",
    "Ferrari", "Esposito", "Ricci", "Romano", "Möller", "Köhler", "Bäcker", "Schröder",
    "Nagy", "Kovács", "Tóth", "Szabó", "Şahin", "Yılmaz", "Özdemir", "Çelik", "Kaya",
    "Çavuşoğlu", "İnan", "Öztürk", "Dubois", "Leroy", "Petit", "François", "Roux",
    "Gautier", "Lefèvre", "Nakatani", "Yamamoto", "Kawasaki", "Ishikawa", "Popescu",
    "Avram", "Dumitru", "Constantinescu", "Dăscălescu", "Pană", "Bălan", "Năstase",
    "O'Neill", "O'Connor", "McCarthy", "O'Sullivan", "O'Brien", "McGuire", "Björklund",
    "Sandström", "Bergström", "Sjöberg", "Lundqvist", "Höglund", "Ásgeirsson", "Þórsson",
    "Harðarson", "Jónsdóttir", "Þorsteinsson", "Magnússon", "van der Walt", "van Rooyen",
    "du Plessis", "van Niekerk", "le Roux", "Dragić", "Stanković", "Jovanović", "Petrović",
    "Đurić", "Knežević", "Božić", "Jurić"
]

# Compound surnames (separated by space or hyphen)
COMPOUND_CONNECTORS = [" ", "-"]
COMPOUND_PROB = 0.25  # 25% chance of having a compound surname

def normalize_for_email(text):
    """Convert accented characters to their ASCII equivalent for email addresses."""
    # Normalize to NFKD form and remove combining characters
    normalized = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Convert to lowercase and replace spaces or hyphens with dots
    normalized = normalized.lower().replace(' ', '.').replace('-', '.')
    return normalized

def generate_surname():
    """Generate a random surname, possibly compound with diacritics."""
    if random.random() < COMPOUND_PROB:  # 25% chance for compound surname
        surname1 = random.choice(SURNAMES)
        surname2 = random.choice(SURNAMES)
        connector = random.choice(COMPOUND_CONNECTORS)
        return f"{surname1}{connector}{surname2}"
    else:
        return random.choice(SURNAMES)

def generate_unique_id():
    """Generate a unique placeholder for hrc_id."""
    return f"placeholder-{uuid.uuid4().hex[:8]}"

def ensure_output_dir():
    """Make sure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def anonymize_presenter_data():
    """Anonymize the presenter data and update the videos accordingly."""
    # Make sure output directory exists
    ensure_output_dir()
    
    # Load presenters data
    if os.path.exists(PRESENTERS_INPUT):
        with open(PRESENTERS_INPUT, 'r') as f:
            presenters_data = json.load(f)
        print(f"Loaded presenter data from: {PRESENTERS_INPUT}")
    else:
        print(f"Error: Presenters file not found at {PRESENTERS_INPUT}")
        return False

    # Get random portraits for all presenters
    portrait_urls = get_random_portraits(len(presenters_data))
    
    # Load videos data
    if os.path.exists(VIDEOS_INPUT):
        with open(VIDEOS_INPUT, 'r') as f:
            videos_data = json.load(f)
        print(f"Loaded video data from: {VIDEOS_INPUT}")
    else:
        print(f"Error: Videos file not found at {VIDEOS_INPUT}")
        return False
        
    # Copy other JSON files if they exist
    if os.path.exists(TAGS_INPUT):
        with open(TAGS_INPUT, 'r') as f:
            tags_data = json.load(f)
        print(f"Loaded tags data from: {TAGS_INPUT}")
    else:
        tags_data = None
        print(f"Note: Tags file not found at {TAGS_INPUT}")
        
    if os.path.exists(TAG_CATEGORIES_INPUT):
        with open(TAG_CATEGORIES_INPUT, 'r') as f:
            tag_categories_data = json.load(f)
        print(f"Loaded tag categories data from: {TAG_CATEGORIES_INPUT}")
    else:
        tag_categories_data = None
        print(f"Note: Tag categories file not found at {TAG_CATEGORIES_INPUT}")

    # Map of original names to anonymized names
    name_mapping = {}
    
    # Process all presenters
    for i, presenter in enumerate(presenters_data):
        # Generate unique placeholder for hrc_id
        presenter["hrc_id"] = generate_unique_id()
        
        # Get the original name and extract first name
        original_name = presenter["name"]
        name_parts = original_name.split(' ')
        
        # Preserve the first name(s) and replace the surname(s)
        if len(name_parts) >= 2:
            # Determine how many parts are the first name vs last name
            # Assume last 1-2 words are surname(s)
            first_name_parts = name_parts[:-1]  # By default, assume last word is surname
            
            # Generate new surname
            new_surname = generate_surname()
            
            # Create new full name
            new_name = " ".join(first_name_parts) + " " + new_surname
            
            # Update the email
            email_parts = presenter["email"].split('@')
            if len(email_parts) == 2:
                domain = email_parts[1]
                first_name_email = normalize_for_email(" ".join(first_name_parts))
                surname_email = normalize_for_email(new_surname)
                new_email = f"{first_name_email}.{surname_email}@{domain}"
                presenter["email"] = new_email
            
            # Replace headshot URL with a random portrait
            presenter["headshot"] = portrait_urls[i]
            
            # Save the mapping and update the presenter
            name_mapping[original_name] = new_name
            presenter["name"] = new_name

    # Update the references in videos.json
    for video in videos_data:
        if "presenters" in video and isinstance(video["presenters"], list):
            for i, presenter_name in enumerate(video["presenters"]):
                if presenter_name in name_mapping:
                    video["presenters"][i] = name_mapping[presenter_name]

    # Save the updated files
    try:
        with open(PRESENTERS_OUTPUT, 'w') as f:
            json.dump(presenters_data, f, indent=2)
        print(f"Successfully anonymized presenter data in {PRESENTERS_OUTPUT}")
        
        with open(VIDEOS_OUTPUT, 'w') as f:
            json.dump(videos_data, f, indent=2)
        print(f"Successfully updated presenter references in {VIDEOS_OUTPUT}")
        
        # Save other files if they were loaded
        if tags_data:
            with open(TAGS_OUTPUT, 'w') as f:
                json.dump(tags_data, f, indent=2)
            print(f"Copied tags data to {TAGS_OUTPUT}")
            
        if tag_categories_data:
            with open(TAG_CATEGORIES_OUTPUT, 'w') as f:
                json.dump(tag_categories_data, f, indent=2)
            print(f"Copied tag categories data to {TAG_CATEGORIES_OUTPUT}")
            
    except Exception as e:
        print(f"Error saving files: {e}")
        return False

    return True

if __name__ == "__main__":
    import sys
    
    print("This script will anonymize presenter data and update video references.")
    print(f"Reading from: {INPUT_DIR}")
    print(f"Writing to: {OUTPUT_DIR}")
    
    response = input("Do you want to continue? (y/n): ")
    if response.lower() == 'y':
        if anonymize_presenter_data():
            print("\nData anonymization complete!")
    else:
        print("Operation cancelled.") 
import os
import requests
import logging
from webapp.database import db_session
from models.presenter import Presenter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_directory_data():
    """Fetch employee data from the directory API"""
    url = "https://directory.wpe.internal/graphql/"
    headers = {
        "authorization": f"token {os.getenv('DIRECTORY_API_TOKEN')}",
        "content-type": "application/json",
    }
    
    query = {
        "operationName": None,
        "variables": {},
        "query": "{  employees {    name    hrcId    email    avatar  }}"
    }
    
    try:
        # Disable SSL verification warnings since we're ignoring cert
        requests.packages.urllib3.disable_warnings()
        
        response = requests.post(
            url, 
            json=query,
            headers=headers,
            verify=False  # Ignore SSL certificate verification
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch directory data: {e}")
        return None

def update_presenters():
    """Update presenter information in the database"""
    data = get_directory_data()
    if not data or 'data' not in data or 'employees' not in data['data']:
        logger.error("Invalid data received from API")
        return

    try:
        employees = data['data']['employees']
        updated_count = 0
        new_count = 0

        for employee in employees:
            # Generate headshot URL
            # TODO: Waiting on https://github.com/canonical/directory-api/issues/88 to return base64 encoded avatar data from API, 
            # so for now we're using the canonical.com avatar endpoint.

            headshot_url = f"https://directory.canonical.com/avatar/{employee['email']}"
            
            # First try to find presenter by HRC ID
            presenter = db_session.query(Presenter).filter_by(hrc_id=employee['hrcId']).first()
            
            # If not found by HRC ID, try to find by email
            if not presenter:
                presenter = db_session.query(Presenter).filter(
                    Presenter.email == employee['email']
                ).first()
            
            if presenter:
                # Check if any data has changed
                has_changes = (
                    presenter.name != employee['name'] or
                    presenter.email != employee['email'] or
                    presenter.hrc_id != employee['hrcId'] or
                    presenter.headshot != headshot_url
                )
                
                if has_changes:
                    # Update existing presenter
                    presenter.name = employee['name']
                    presenter.email = employee['email']
                    presenter.hrc_id = employee['hrcId']
                    presenter.headshot = headshot_url
                    updated_count += 1
                    logger.info(f"Updated presenter: {presenter.email} (HRC ID: {presenter.hrc_id})")
            else:
                # Create new presenter
                presenter = Presenter(
                    name=employee['name'],
                    email=employee['email'],
                    hrc_id=employee['hrcId'],
                    headshot=headshot_url
                )
                db_session.add(presenter)
                new_count += 1
                logger.info(f"Created new presenter: {presenter.email}")
        
        if updated_count > 0 or new_count > 0:
            db_session.commit()
            logger.info(f"Successfully updated {updated_count} and created {new_count} presenters")
        return True
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error updating presenters: {e}")
        raise

if __name__ == "__main__":
    update_presenters() 
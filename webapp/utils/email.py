import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from google.auth.exceptions import GoogleAuthError

logger = logging.getLogger(__name__)

# TODO: This whole thing needs to be reworked to send emails differently.
# Do not use this function without a rework.

def send_admin_notification(submission):
    """Send email notification to admins about new submission using Gmail API."""
    
    # Get admin emails from environment variable
    admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
    if not admin_emails:
        logger.error("No admin emails configured")
        raise ValueError("ADMIN_EMAILS environment variable not set")

    try:
        # Load credentials from environment
        required_env_vars = [
            'GOOGLE_PROJECT_ID', 'PRIVATE_KEY_ID', 'PRIVATE_KEY',
            'CLIENT_EMAIL', 'CLIENT_ID', 'CLIENT_X509_CERT_URL',
            'GMAIL_DELEGATE_ACCOUNT'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        credentials_dict = {
            "type": "service_account",
            "project_id": os.getenv('GOOGLE_PROJECT_ID'),
            "private_key_id": os.getenv('PRIVATE_KEY_ID'),
            "private_key": os.getenv('PRIVATE_KEY').replace('\\n', '\n'),
            "client_email": os.getenv('CLIENT_EMAIL'),
            "client_id": os.getenv('CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv('CLIENT_X509_CERT_URL')
        }

        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=['https://www.googleapis.com/auth/gmail.send']
        )

        delegated_credentials = credentials.with_subject(os.getenv('GMAIL_DELEGATE_ACCOUNT'))
        service = build('gmail', 'v1', credentials=delegated_credentials)

        message = MIMEText(f"""
        A new Masterclass submission has been received:
        
        Title: {submission.title}
        Submitted by: {submission.email}
        Duration: {submission.duration}
        
        Description:
        {submission.description}
        
        View all submissions in the admin panel: {os.getenv('BASE_URL', '')}/admin/masterclasssubmission/
        """)

        message['to'] = ', '.join(admin_emails)
        message['from'] = os.getenv('GMAIL_DELEGATE_ACCOUNT')
        message['subject'] = f'New Masterclass Submission: {submission.title}'

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        try:
            service.users().messages().send(userId='me', body={'raw': raw}).execute()
            logger.info(f"Email notification sent for submission: {submission.title}")
            return True
        except Exception as e:
            logger.error(f"Gmail API error: {str(e)}")
            raise

    except GoogleAuthError as e:
        logger.error(f"Google authentication error: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in send_admin_notification: {str(e)}")
        raise
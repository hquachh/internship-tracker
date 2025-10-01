"""
Scrape Starred Emails:
    - authenticate with gmail api
    - fetch all starred emails
    - parse fields
    - insert into sqlite database with label submitted
"""

import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from src.config.db_utils import insert_email

# path to your gmail credentials, update if needed
TOKEN_PATH = "src/config/gmail_token.json"
CREDS_PATH = "src/config/gmail_config.json"

def get_gmail_service():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    service = build("gmail", "v1", credentials=creds)
    return service

def get_body_from_payload(payload):
    # recursive function to walk through MIME parts
    if "body" in payload and "data" in payload["body"] and payload["body"]["data"]:
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    
    if "parts" in payload:
        for part in payload["parts"]:
            text = get_body_from_payload(part)
            if text:
                return text

    return ""

def parse_message(msg, starred=False):
    msg_id = msg["id"]
    payload = msg.get("payload", {})
    headers = payload.get("headers", [])

    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "")

    # use recursive search to find first text content
    body = get_body_from_payload(payload)

    return {
        "id": msg_id,
        "subject": subject,
        "sender": sender,
        "body": body,
        "is_starred": starred,
        "label": "Submitted" if starred else "Not Submitted"
    }

def scrape_starred():
    # fetch all starred emails and insert into database
    service = get_gmail_service()
    
    next_page_token = None
    while True:
        results = service.users().messages().list(
            userId="me",
            q="is:starred",
            maxResults=100,
            pageToken=next_page_token
        ).execute()
    
        messages = results.get("messages", [])
        for m in messages:
            msg = service.users().messages().get(userId="me", id=m["id"]).execute()
            email_data = parse_message(msg, starred=True)
            insert_email(email_data)

        next_page_token = results.get("nextPageToken")
        if not next_page_token:
            break
    
if __name__ == "__main__":
    scrape_starred()
    print("Starred emails scraped and inserted into database")

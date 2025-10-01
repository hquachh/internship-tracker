"""
Scrape Recent Emails:
    - authenticate with gmail api
    - fetch last ~800 emials
    - skip starred emails
    - insert unstarred emails
"""

import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from src.config.db_utils import insert_email

TOKEN_PATH = "src/config/gmail_token.json"

def get_gmail_service():
    # connect to gmail api using stored credentials
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

def scrape_recent():
    # fetch last ~800 emails and insert into database
    service = get_gmail_service()
    next_page_token = None
    fetched = 0
    limit = 800

    while True and fetched < limit:
        results = service.users().messages().list(
            userId="me",
            maxResults=10,
            pageToken=next_page_token
        ).execute()

        messages = results.get("messages", [])
        for m in messages:
            if fetched >= limit:
                break
            msg = service.users().messages().get(userId="me", id=m["id"]).execute()

            if "STARRED" in msg.get("labelIds", []):
                continue
            
            email_data = parse_message(msg, starred=False)
            insert_email(email_data)
            fetched += 1
        
        next_page_token = results.get("nextPageToken")
        if not next_page_token or fetched >= limit:
            break

    print(f"Inserted {fetched} recent unstarred emails as Not Submited")

if __name__ == "__main__":
    scrape_recent()
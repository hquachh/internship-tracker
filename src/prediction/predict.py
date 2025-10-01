"""
Predict + Update:
    - load saved model + vectorizers
    - fetch new emails
    - preprocess subject/body + sender domain
    - classify as Submitted vs Not Submitted
    - insert new Submitted apps into Google Sheet
"""

import os
import re
import joblib
import sqlite3
import pandas as pd
from scipy.sparse import hstack
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from src.preprocessing.clean_text import clean_text
from src.prediction.update_sheets import update_sheet
from src.ai_extraction.extract_info import extract_with_ai

DB_PATH = "internship.db"
TOKEN_PATH = "src/config/gmail_token.json"
MODEL_DIR = "models"

DEFAULT_START_DATE = "2025/08/05"  # Fallback date for first run

def get_gmail_service():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    return build("gmail", "v1", credentials=creds)

def extract_domain(sender):
    if not isinstance(sender, str) or "@" not in sender:
        return "unknown"
    dom = sender.split("@")[-1].lower()
    parts = dom.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else dom

def get_dynamic_query():
    """Get the query date based on the latest date in the sheet, minus 1 day."""
    try:
        from src.prediction.update_sheets import get_service, SPREADSHEET_ID
        service = get_service()

        # Get all dates from the sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!E:E"  # Date Received column
        ).execute()

        values = result.get('values', [])

        if len(values) <= 1:  # Only headers or empty sheet
            print(f"[INFO] First run detected, using default start date: {DEFAULT_START_DATE}")
            return f"after:{DEFAULT_START_DATE}"

        # Parse dates and find the latest one
        from datetime import datetime, timedelta
        import re

        latest_date = None
        for row in values[1:]:  # Skip header
            if row and row[0] and row[0] != "[Please Enter]":
                date_str = row[0]
                try:
                    # Parse MM-DD-YYYY format
                    if re.match(r'\d{1,2}-\d{1,2}-\d{4}', date_str):
                        date_obj = datetime.strptime(date_str, "%m-%d-%Y")
                        if latest_date is None or date_obj > latest_date:
                            latest_date = date_obj
                except:
                    continue

        if latest_date:
            # Use the same date (don't subtract 1 day) and format for Gmail query
            query_str = latest_date.strftime("%Y/%m/%d")
            print(f"[INFO] Latest date in sheet: {latest_date.strftime('%m-%d-%Y')}, querying from: {query_str}")
            return f"after:{query_str}"
        else:
            print(f"[INFO] No valid dates found in sheet, using default start date: {DEFAULT_START_DATE}")
            return f"after:{DEFAULT_START_DATE}"

    except Exception as e:
        print(f"[INFO] Could not determine dynamic date ({e}), using default: {DEFAULT_START_DATE}")
        return f"after:{DEFAULT_START_DATE}"

def fetch_emails():
    # pull emails since cutoff date (get all emails, not just 200)
    query = get_dynamic_query()
    service = get_gmail_service()
    msgs = []
    next_page_token = None
    total_fetched = 0

    print(f"[INFO] Starting email fetch with query: {query}")

    while True:
        max_results = 500
        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
            pageToken=next_page_token
        ).execute()

        batch_count = 0
        for m in results.get("messages", []):
            msg = service.users().messages().get(userId="me", id=m["id"]).execute()
            payload = msg.get("payload", {})
            headers = payload.get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "")
            date = next((h["value"] for h in headers if h["name"] == "Date"), "")
            body = _get_body(payload)

            msgs.append(
                {
                    "id": m["id"],
                    "subject": subject,
                    "sender": sender,
                    "date": date,
                    "body": body,
                }
            )

            batch_count += 1
            total_fetched += 1

            # Progress indicator every 100 emails
            if total_fetched % 100 == 0:
                print(f"[INFO] {total_fetched} emails fetched...")

        # Show progress for smaller batches too
        if batch_count > 0:
            print(f"[INFO] Batch complete: {batch_count} emails processed (total: {total_fetched})")

        # Check if there are more pages
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break

        print(f"[DEBUG] Fetched {len(msgs)} emails so far, getting more...")

    return msgs

def _get_body(payload):
    # recursive parse mime parts
    if "body" in payload and "data" in payload["body"] and payload["body"]["data"]:
        import base64
    
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    if "parts" in payload:
        for part in payload["parts"]:
            text = _get_body(part)
            if text:
                return text
    return ""

def dedupe_new(emails):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create tables if they don't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emails_raw (
            id TEXT PRIMARY KEY,
            subject TEXT,
            sender TEXT,
            date TEXT,
            body TEXT
        )
    """)

    # Track emails that have been processed and added to sheets
    cur.execute("""
        CREATE TABLE IF NOT EXISTS processed_applications (
            email_id TEXT PRIMARY KEY,
            company TEXT,
            position TEXT,
            date_processed TEXT,
            FOREIGN KEY (email_id) REFERENCES emails_raw (id)
        )
    """)
    conn.commit()

    # Get emails already in database
    existing = pd.read_sql("SELECT id FROM emails_raw", conn)
    seen_in_db = set(existing["id"].tolist())

    # Get emails already processed into applications
    processed = pd.read_sql("SELECT email_id FROM processed_applications", conn)
    processed_emails = set(processed["email_id"].tolist())

    # Filter out emails that are already in database
    fresh = [e for e in emails if e["id"] not in seen_in_db]

    # Insert all new emails into db
    for e in fresh:
        cur.execute(
            "INSERT OR IGNORE INTO emails_raw (id, subject, sender, date, body) VALUES (?, ?, ?, ?, ?)",
            (e["id"], e["subject"], e["sender"], e["date"], e["body"]),
        )

    # Also filter out emails that were already processed into applications
    # This prevents the same email from being classified and added to sheets multiple times
    truly_new = [e for e in fresh if e["id"] not in processed_emails]

    conn.commit()
    conn.close()

    print(f"[DEBUG] {len(emails)} total emails, {len(fresh)} new in database, {len(truly_new)} not yet processed")
    return truly_new


def build_features(emails, tfidf_subject, tfidf_body, domain_encoder):
    subs = [clean_text(e["subject"]) for e in emails]
    bods = [clean_text(e["body"]) for e in emails]
    doms = [extract_domain(e["sender"]) for e in emails]

    X_sub = tfidf_subject.transform(subs)
    X_body = tfidf_body.transform(bods)
    # Map domains to known categories or "other"
    mapped_doms = []
    for d in doms:
        if hasattr(domain_encoder, 'categories_') and len(domain_encoder.categories_) > 0:
            if d in domain_encoder.categories_[0]:
                mapped_doms.append([d])
            else:
                mapped_doms.append(["other"])
        else:
            mapped_doms.append([d])
    X_dom = domain_encoder.transform(mapped_doms)
    return hstack([X_sub, X_body, X_dom])

def extract_company_position(subject, body, sender=""):
    """
    Enhanced extraction using AI wrapper with regex fallback.
    Returns (company, position) tuple for backward compatibility.
    """
    try:
        result = extract_with_ai(subject, body, sender)
        return result['company'], result['position']
    except Exception as e:
        print(f"[DEBUG] AI extraction failed, using legacy regex: {e}")
        # Fallback to original regex logic (simplified version)
        full_text = f"{subject} {body}".lower()

        # Simple regex patterns for fallback
        company_match = re.search(r"(?:from|at)\s+([A-Za-z][A-Za-z\s&.-]+?)(?:\s+for|\.|$)", full_text, re.IGNORECASE)
        company = company_match.group(1).strip().title() if company_match else ""

        position_match = re.search(r"(?:for|as)\s+(?:the\s+)?([a-z\s]*(?:intern|internship|engineer|analyst)[a-z\s]*)", full_text, re.IGNORECASE)
        position = position_match.group(1).strip().title() if position_match else ""

        return company, position

def extract_enhanced_info(subject, body, sender=""):
    """
    Extract full information including candidate portal URL.
    Returns dict with company, position, and candidate_portal_url.
    """
    return extract_with_ai(subject, body, sender)

def classify(emails):
    print("[INFO] Loading ML model and vectorizers...")
    # load model + vectorizers
    model = joblib.load(os.path.join(MODEL_DIR, "log_reg.pkl"))
    tfidf_subject = joblib.load(os.path.join(MODEL_DIR, "tfidf_subject.pkl"))
    tfidf_body = joblib.load(os.path.join(MODEL_DIR, "tfidf_body.pkl"))
    domain_encoder = joblib.load(os.path.join(MODEL_DIR, "domain_encoder.pkl"))

    print(f"[INFO] Classifying {len(emails)} emails...")
    X = build_features(emails, tfidf_subject, tfidf_body, domain_encoder)
    preds = model.predict(X)

    # Count predictions
    submitted_count = sum(preds)
    print(f"[INFO] Classification complete: {submitted_count}/{len(emails)} emails classified as submitted")

    submitted = []
    processed_count = 0

    print("[INFO] Starting AI extraction for submitted applications...")
    for e, p in zip(emails, preds):
        if p == 1:
            processed_count += 1
            print(f"[INFO] Processing application {processed_count}/{submitted_count}: {e['subject'][:50]}...")

            # extract enhanced information including candidate portal URL
            enhanced_info = extract_enhanced_info(e["subject"], e["body"], e.get("sender", ""))

            # Show extraction results
            company = enhanced_info.get("company", "")
            position = enhanced_info.get("position", "")
            method = enhanced_info.get("extraction_method", "unknown")

            submitted.append(
                {
                    "email_id": e["id"],  # Include email ID for tracking
                    "date": e["date"],
                    "company": company,
                    "position": position,
                    "candidate_portal_url": enhanced_info.get("candidate_portal_url", ""),
                    "extraction_method": method
                }
            )

    print(f"[INFO] AI extraction complete! {len(submitted)} applications ready for Google Sheets")
    return submitted

def record_processed_applications(submitted_apps, email_mapping):
    """Record which emails have been successfully processed into applications."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    from datetime import datetime
    current_time = datetime.now().isoformat()

    for app in submitted_apps:
        # Find the corresponding email ID (this requires modifying the classification process)
        email_id = app.get('email_id')
        if email_id:
            cur.execute("""
                INSERT OR REPLACE INTO processed_applications
                (email_id, company, position, date_processed)
                VALUES (?, ?, ?, ?)
            """, (email_id, app.get('company', ''), app.get('position', ''), current_time))

    conn.commit()
    conn.close()
    print(f"[DEBUG] Recorded {len(submitted_apps)} processed applications in database")

def predict_and_update():
    raw = fetch_emails()
    print(f"[DEBUG] Fetched {len(raw)} total emails")

    new_emails = dedupe_new(raw)
    print(f"[DEBUG] {len(new_emails)} new emails after deduplication")

    if not new_emails:
        print("[INFO] no new emails found")
        return

    # Show first few email subjects for debugging
    for i, email in enumerate(new_emails[:3]):
        print(f"[DEBUG] Email {i+1}: {email['subject'][:50]}...")

    submitted_apps = classify(new_emails)
    print(f"[DEBUG] {len(submitted_apps)} emails classified as submitted")

    if not submitted_apps:
        print("[INFO] no new submitted applications")
        return

    update_sheet(submitted_apps)

    # Record the applications as processed to prevent future duplicates
    record_processed_applications(submitted_apps, {})

    print(f"[INFO] added {len(submitted_apps)} new submitted applications")

def main():
    predict_and_update()

if __name__ == "__main__":
    main()










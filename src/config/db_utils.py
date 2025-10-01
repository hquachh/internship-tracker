"""
Database Utils:
    - connect to sqlite database
    - insert single or multiple emails
    - fetch all emails
"""

import sqlite3
from typing import Dict, Any, List

DB_PATH = "internship.db"

def get_connection():
    # open connection to sqlite database
    return sqlite3.connect(DB_PATH)

def insert_email(email: Dict[str, Any]):
    # insery single email into database, ignore if id already exists
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO emails (id, subject, sender, body, is_starred, label)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            email["id"],
            email["subject"],
            email["sender"],
            email["body"],
            email["is_starred"],
            email["label"]
        ))
    conn.commit()
    conn.close()

def insert_emails(emails: List[Dict[str, Any]]):
    # insert multiple emails at once
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany("""
        INSERT OR IGNORE INTO emails (id, subject, sender, body, is_starred, label)
        VALUES (?, ?, ?, ?, ?, ?)
        """, [
                    (
            email["id"],
            email["subject"],
            email["sender"],
            email["body"],
            email["is_starred"],
            email["label"]
        )
        for email in emails
        ])
    conn.commit()
    conn.close()

def fetch_all():
    # return all emails currently in database
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM emails")
    rows = cur.fetchall()
    conn.close()
    return rows
"""
Build Dataset:
    - load emails from sqlite
    - remove duplicates
    - clean and normalize text
    - verify labels and report counts
    - split into train/val/test
    - update database with processed table
"""

import os
import json
import pandas as pd
import sqlite3
from sklearn.model_selection import train_test_split
from .clean_text import clean_text

DEFAULT_DB_PATH = "internship.db"
CFG_PATH = os.path.join("src", "config", "db_config.json")
OUTPUT_DIR = "data"

def get_db_path():
    # try to read db path from config
    if os.path.exists(CFG_PATH):
        try:
            with open(CFG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg.get("sqlite_path", DEFAULT_DB_PATH)
        except Exception:
            return DEFAULT_DB_PATH
    return DEFAULT_DB_PATH

def load_emails(db_path):
    # pull all emails from db
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM emails", conn)
    conn.close()
    return df

def remove_duplicates(df):
    # drop duplicate rows by subject+body
    return df.drop_duplicates(subset=["subject", "body"])

def add_processed_text(df):
    # build procesed_text column from subject+body
    df["processed_text"] = (
        df["subject"].fillna("") + df["body"].fillna("")
    ).apply(clean_text)
    return df

def verify_labels(df):
    # filter invalid labels and print distribution
    valid = {"Submitted", "Not Submitted"}
    mask = df["label"].isin(valid)
    bad = (~mask).sum()
    if bad:
        print(f"warning: {bad} rows with invalid labels skipped")
    print(df[mask]["label"].value_counts())
    return df[mask].copy()

def split_and_save(df):
    # split into train/val/test and save csvs
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    train, temp = train_test_split(df, test_size=0.3, stratify=df["label"], random_state=42)
    val, test = train_test_split(temp, test_size=0.5, stratify=temp["label"],  random_state=42)
    train.to_csv(os.path.join(OUTPUT_DIR, "train.csv"), index=False)
    val.to_csv(os.path.join(OUTPUT_DIR, "val.csv"), index=False)
    test.to_csv(os.path.join(OUTPUT_DIR, "test.csv"), index=False)

def save_to_db(df, db_path):
    # write processed table back into db
    conn = sqlite3.connect(db_path)
    df.to_sql("emails_processed", conn, if_exists="replace", index=False)
    conn.close()

def main():
    db_path = get_db_path()
    df = load_emails(db_path)
    df = remove_duplicates(df)
    df = add_processed_text(df)
    df_ok = verify_labels(df)
    split_and_save(df_ok)
    save_to_db(df, db_path)
    print("dataset build complete")

if __name__ == "__main__":
    main()
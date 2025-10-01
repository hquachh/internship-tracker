"""
Train Model:
    - load train/val/test csv
    - extract sender domains
    - vectorize subject/body with TF-IDF
    - one-hot encode sender domains (top 50 + other)
    - combine features and train logistic regression
    - evaluate on val/test sets
    - save model + vectorizers for later prediction
"""

import os
import re
import joblib
import pandas as pd
from collections import Counter
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

DATA_DIR = "data"
MODEL_DIR = "models"

def load_data():
    # read train/val/test splits
    train = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    val = pd.read_csv(os.path.join(DATA_DIR, "val.csv"))
    test = pd.read_csv(os.path.join(DATA_DIR, "test.csv"))
    return train, val, test

def extract_domain(sender):
    # pull domain from email address
    if not isinstance(sender, str) or "@" not in sender:
        return "unknown"
    dom = sender.split("@")[-1].lower()
    # strip subdomains 
    parts = dom.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else dom

def prepare_domains(train, val, test, top_k=50):
    # map sender -> domain
    train["domain"] = train["sender"].apply(extract_domain)
    val["domain"] = val["sender"].apply(extract_domain)
    test["domain"] = test["sender"].apply(extract_domain)

    # pick top-k frequent domains
    counts = Counter(train["domain"])
    top_domains = [d for d, _ in counts.most_common(top_k)]

    # replace rare with "other"
    def normalize_domain(d):
        return d if d in top_domains else "other"
    
    train["domain_norm"] = train["domain"].apply(normalize_domain)
    val["domain_norm"] = val["domain"].apply(normalize_domain)
    test["domain_norm"] = test["domain"].apply(normalize_domain)

    # one-hot encode
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    X_train = encoder.fit_transform(train[["domain_norm"]])
    X_val = encoder.transform(val[["domain_norm"]])
    X_test = encoder.transform(test[["domain_norm"]])

    return encoder, X_train, X_val, X_test

def vectorize_text(train, val, test):
    # tf-idf on subject
    tfidf_subject = TfidfVectorizer(max_features=1000, ngram_range=(1,2))
    X_train_sub = tfidf_subject.fit_transform(train["subject"].fillna(""))
    X_val_sub = tfidf_subject.transform(val["subject"].fillna(""))
    X_test_sub = tfidf_subject.transform(test["subject"].fillna(""))

    # tf-idf on processed_text
    tfidf_body = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
    X_train_body = tfidf_body.fit_transform(train["processed_text"].fillna(""))
    X_val_body = tfidf_body.transform(val["processed_text"].fillna(""))
    X_test_body = tfidf_body.transform(test["processed_text"].fillna(""))
    
    return tfidf_subject, tfidf_body, X_train_sub, X_val_sub, X_test_sub, X_train_body, X_val_body, X_test_body

def labels_to_binary(df):
    # map labels to 1 or 0
    return (df["label"] == "Submitted").astype(int)

def train_model(X_train, y_train):
    # logistic regression with balanced class weights
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X_train, y_train)
    return clf

def evaluate(model, X, y, split_name):
    preds = model.predict(X)
    print(f"\n--- {split_name} performance ---")
    print(classification_report(y, preds, target_names=["Not Submitted", "Submitted"]))

def save_artifacts(model, tfidf_subject, tfidf_body, domain_encoder):
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODEL_DIR, "log_reg.pkl"))
    joblib.dump(tfidf_subject, os.path.join(MODEL_DIR, "tfidf_subject.pkl"))
    joblib.dump(tfidf_body, os.path.join(MODEL_DIR, "tfidf_body.pkl"))
    joblib.dump(domain_encoder, os.path.join(MODEL_DIR, "domain_encoder.pkl"))
    print("\n[INFO] saved model + vectorizers into models/")

def main():
    # load data
    train, val, test = load_data()

    # vectorize domains
    domain_encoder, X_train_dom, X_val_dom, X_test_dom = prepare_domains(train, val, test)

    # vectorize text
    tfidf_subject, tfidf_body, X_train_sub, X_val_sub, X_test_sub, X_train_body, X_val_body, X_test_body = vectorize_text(train, val, test)

    # combine features
    X_train = hstack([X_train_sub, X_train_body, X_train_dom])
    X_val = hstack([X_val_sub, X_val_body, X_val_dom])
    X_test = hstack([X_test_sub, X_test_body, X_test_dom])

    # labels
    y_train = labels_to_binary(train)
    y_val = labels_to_binary(val)
    y_test = labels_to_binary(test)

    # train
    model = train_model(X_train, y_train)

    # eval
    evaluate(model, X_val, y_val, "Validation")
    evaluate(model, X_test, y_test, "Test")

    # save
    save_artifacts(model, tfidf_subject, tfidf_body, domain_encoder)

if __name__ == "__main__":
    main()









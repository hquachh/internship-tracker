- 1. Purpose

To automatically detect internship/job application confirmation emails in Gmail and record them into a structured Google Sheet, so users don’t have to manually track applications.

MVP = single-user (you).

Future = scalable to multiple users via a web app.

2. Goals

Automatically collect confirmation emails.

Export to Google Sheets with structured fields.

Avoid duplicates, preserve user edits.

Separate applications by internship year (e.g., Summer 2025 vs Summer 2026).

3. Non-Goals (MVP)

No UI beyond CLI/script.

No multi-class classification (rejections, interviews) yet.

No cloud hosting (local script only).

4. User Flow (MVP)

User runs the script (first run).

Authenticates Gmail + Google Sheets (OAuth).

Script creates a new Google Sheet from template.

Script fetches application-season emails (e.g., Fall 2025 → Summer 2026).

Model classifies each as Submitted vs Not Submitted.

Appends results into Google Sheet.

On later runs, script:

Deduplicates using message_id.

Only appends new confirmations.

Leaves user edits (Location, Compensation, Notes) untouched.

5. Data Strategy

Training data:

Positives = user-starred confirmation emails.

Negatives = ~500 recent unstarred emails (deduped).

Feature engineering:

Subject → TF-IDF (1–2 grams).

Body → TF-IDF (1–2 grams).

Sender domain → One-hot.

Model: Logistic Regression (baseline).

Storage: SQL database (internship_tracker) with 4 tables:

emails_raw (all Gmail pulls).

training_labels (submitted vs not).

applications (structured tracker).

users (future scalability).

6. Google Sheet Template

Columns:

Date Received

Company

Position

Internship Year

Location (manual)

Compensation (manual)

Status (auto = Submitted)

Notes (manual)

7. Phases & Deliverables
Phase 1 — Setup

Create SQL database + tables.

Define Google Sheet template.

Phase 2 — Data Collection

Fetch starred (positives) + ~500 unstarred (negatives).

Store in emails_raw.

Label into training_labels.

Phase 3 — Preprocessing

Clean subject/body.

Extract sender domain.

Build vectorizers.

Phase 4 — Modeling

Train/test split (80/20).

Train Logistic Regression.

Save model.

Phase 5 — MVP Script

Authenticate Gmail/Sheets.

Fetch emails for application season.

Deduplicate by message_id.

Preprocess → classify → append to Google Sheet.

Phase 6 — Validation

Manual check of classifications.

Iterative improvements (active learning).

Phase 7 — Future

DistilBERT upgrade (2k+ dataset).

Multi-class classification (Submitted, Rejected, Interview, Offer).

Web app + multi-user support.

8. Success Metrics

MVP:

≥85% precision & recall on classification.

Script completes run in <2 minutes for ~1000 emails.

No duplicate entries in Google Sheet.

Future:

Multi-user web app with OAuth.

Support >100 users with smooth performance.\
\
This is my project. This what we refer to from now on with most information on how I want this project to work
CREATE TABLE emails(
    id TEXT PRIMARY KEY, -- gmail message_id
    subject TEXT,
    sender TEXT,
    body TEXT,
    is_starred BOOLEAN,
    label TEXT -- "Submitted" or "Not Submitted"
);
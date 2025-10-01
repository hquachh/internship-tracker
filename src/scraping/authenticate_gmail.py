"""
Authenticate Gmail:
    - run oauth flow with gmail api
    - generate and save token file
    - used for later scraping scripts

"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


CREDS_PATH = "src/config/gmail_config.json"
TOKEN_PATH = "src/config/gmail_token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def authenticate():
    creds = None

    # load existing token if it exists
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # refresh token if expired, otherwise run full auth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server()

        # save the new token for future runs

        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    print("Authentication complete. Token saved at", TOKEN_PATH)

if __name__ == "__main__":
    authenticate()

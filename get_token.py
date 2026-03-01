from __future__ import print_function
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# This bridge only needs access to files it creates or opens.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main():
    creds = None
    creds_path = "credentials.json"  # OAuth client from Google Cloud Console
    token_path = "token.json"        # will be created/updated

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    # Tiny sanity check: print account + quota
    service = build("drive", "v3", credentials=creds)
    about = service.about().get(fields="user, storageQuota").execute()
    print("Login OK. User:", about["user"]["emailAddress"])
    print("Quota:", about["storageQuota"])


if __name__ == "__main__":
    main()

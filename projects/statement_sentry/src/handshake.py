import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
# 'readonly' means we can look at emails but not delete or send them (Security First!)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    # It is created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This looks for the file you downloaded earlier
            flow = InstalledAppFlow.from_client_secrets_file(
                "projects/statement_sentry/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Build the Gmail service
    service = build("gmail", "v1", credentials=creds)

    # Call the Gmail API to fetch the last 10 messages
    results = service.users().messages().list(userId="me", maxResults=10).execute()
    messages = results.get("messages", [])

    if not messages:
        print("No messages found.")
    else:
        print("Connection Successful! Last 10 Email IDs:")
        for message in messages:
            print(f"- Message ID: {message['id']}")


if __name__ == "__main__":
    main()

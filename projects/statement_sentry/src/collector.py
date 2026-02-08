import base64
import os
import re

from config import CARD_CONFIG  # Importing our new config
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        return build("gmail", "v1", credentials=creds)
    return None


def extract_one_card_details(html_body):
    """
    Simple RegEx to find amounts in the One Card email body.
    """
    # Look for patterns like "Total Amount Due: Rs. 5,000.00"
    total_due = re.search(r"Total amount due.*?([\d,]+\.\d{2})", html_body, re.IGNORECASE)
    due_date = re.search(r"Payment due date.*?(\d{1,2}\s\w+\s\d{4})", html_body, re.IGNORECASE)

    return {
        "Total Due": total_due.group(1) if total_due else "Not Found",
        "Due Date": due_date.group(1) if due_date else "Not Found",
    }


def run_collector():
    service = get_gmail_service()
    output_dir = "projects/statement_sentry/data/raw_pdfs"
    os.makedirs(output_dir, exist_ok=True)

    for card_name, info in CARD_CONFIG.items():
        print(f"--- Processing {card_name} ---")
        results = (
            service.users()
            .messages()
            .list(userId="me", q=info["search_query"], maxResults=5)
            .execute()
        )
        messages = results.get("messages", [])

        for msg_ref in messages:
            msg = service.users().messages().get(userId="me", id=msg_ref["id"]).execute()

            if info["type"] == "pdf":
                # Logic for PDF Banks
                for part in msg.get("payload", {}).get("parts", []):
                    if part.get("filename") and part.get("filename").endswith(".pdf"):
                        att_id = part["body"].get("attachmentId")
                        attachment = (
                            service.users()
                            .messages()
                            .attachments()
                            .get(userId="me", messageId=msg_ref["id"], id=att_id)
                            .execute()
                        )

                        file_data = base64.urlsafe_b64decode(attachment["data"].encode("UTF-8"))
                        path = os.path.join(output_dir, f"{card_name}_{part['filename']}")
                        with open(path, "wb") as f:
                            f.write(file_data)
                        print(f"Saved PDF: {path}")

            elif info["type"] == "email_body":
                # Logic for One Card (No PDF)
                # Note: Email body is often in 'parts' or 'body' depending on format
                parts = msg.get("payload", {}).get("parts", [])
                body_data = ""
                if not parts:
                    body_data = msg.get("payload", {}).get("body", {}).get("data", "")
                else:
                    body_data = parts[0].get("body", {}).get("data", "")

                if body_data:
                    decoded_body = base64.urlsafe_b64decode(body_data).decode("utf-8")
                    details = extract_one_card_details(decoded_body)
                    print(f"One Card Data Extracted: {details}")


if __name__ == "__main__":
    run_collector()

import os
import base64
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# -------------------------------------------------------
# PATHS
# -------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials", "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "credentials", "token.json")

# Gmail Read + Modify Permission
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


# -------------------------------------------------------
# AUTHENTICATION
# -------------------------------------------------------

def authenticate_gmail():
    """
    Authenticate Gmail using OAuth.
    Creates token.json only on first login.
    """

    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# -------------------------------------------------------
# READ EMAIL BODY
# -------------------------------------------------------

def extract_email_body(payload):
    """
    Extract plain text body from Gmail payload.
    """

    body = ""

    if "parts" in payload:

        for part in payload["parts"]:

            if part["mimeType"] == "text/plain":

                data = part["body"].get("data")

                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
                    return body

            elif "parts" in part:
                body = extract_email_body(part)
                if body:
                    return body

    else:
        data = payload["body"].get("data")

        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8")

    return body


# -------------------------------------------------------
# FETCH ONLY UNREAD EMAILS
# -------------------------------------------------------

def get_unread_emails(limit=20):
    """
    Fetch unread Gmail emails only.

    Returns list of dictionaries.
    """

    service = authenticate_gmail()

    results = service.users().messages().list(
        userId="me",
        q="is:unread",
        maxResults=limit
    ).execute()

    messages = results.get("messages", [])

    emails = []

    for message in messages:

        msg = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="full"
        ).execute()

        headers = msg["payload"]["headers"]

        subject = ""
        sender = ""
        date = ""

        for h in headers:
            if h["name"] == "Subject":
                subject = h["value"]

            elif h["name"] == "From":
                sender = h["value"]

            elif h["name"] == "Date":
                date = h["value"]

        body = extract_email_body(msg["payload"])

        emails.append({
            "id": message["id"],
            "sender": sender,
            "subject": subject,
            "body": body,
            "received_at": date
        })

    return emails


# -------------------------------------------------------
# MARK EMAIL AS READ
# -------------------------------------------------------

def mark_as_processed(email_id):
    """
    Remove UNREAD label after successful processing.
    Prevents duplicate processing.
    """

    service = authenticate_gmail()

    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={
            "removeLabelIds": ["UNREAD"]
        }
    ).execute()


# -------------------------------------------------------
# CHECK IF NEW EMAIL EXISTS
# -------------------------------------------------------

def has_new_emails():
    """
    Returns True if inbox has unread emails.
    """

    service = authenticate_gmail()

    results = service.users().messages().list(
        userId="me",
        q="is:unread",
        maxResults=1
    ).execute()

    return len(results.get("messages", [])) > 0
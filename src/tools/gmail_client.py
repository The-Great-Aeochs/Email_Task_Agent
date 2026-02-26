"""Gmail API client for fetching and parsing emails."""

import base64
import logging
import re
from datetime import datetime
from email.utils import parseaddr
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.models.task import EmailMessage

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
]


class GmailClient:
    """Fetches and parses emails from Gmail API."""

    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.json",
    ):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth2."""
        creds = None

        try:
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        except FileNotFoundError:
            pass

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail authenticated successfully")

    def fetch_emails(
        self,
        max_results: int = 50,
        query: str = "is:unread",
        label_ids: Optional[list[str]] = None,
    ) -> list[EmailMessage]:
        """Fetch emails from Gmail matching the query."""
        if not self.service:
            self.authenticate()

        try:
            params = {
                "userId": "me",
                "maxResults": max_results,
                "q": query,
            }
            if label_ids:
                params["labelIds"] = label_ids

            results = self.service.users().messages().list(**params).execute()
            messages = results.get("messages", [])

            emails = []
            for msg_ref in messages:
                email = self._fetch_and_parse(msg_ref["id"])
                if email:
                    emails.append(email)

            logger.info(f"Fetched {len(emails)} emails matching query: {query}")
            return emails

        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            return []

    def _fetch_and_parse(self, message_id: str) -> Optional[EmailMessage]:
        """Fetch full message and parse into EmailMessage."""
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}

            # Parse sender
            sender_raw = headers.get("from", "")
            sender_name, sender_email = parseaddr(sender_raw)

            # Parse recipients
            to_raw = headers.get("to", "")
            recipients = [parseaddr(r)[1] for r in to_raw.split(",") if r.strip()]

            # Parse CC
            cc_raw = headers.get("cc", "")
            cc = [parseaddr(r)[1] for r in cc_raw.split(",") if r.strip()]

            # Parse date
            date_str = headers.get("date", "")
            try:
                from email.utils import parsedate_to_datetime
                date = parsedate_to_datetime(date_str)
            except Exception:
                date = datetime.now()

            # Extract body
            body = self._extract_body(msg["payload"])

            # Check for attachments
            has_attachments = self._has_attachments(msg["payload"])

            # Labels
            labels = msg.get("labelIds", [])

            return EmailMessage(
                id=message_id,
                thread_id=msg.get("threadId", message_id),
                subject=headers.get("subject", "(No Subject)"),
                sender=sender_email,
                sender_name=sender_name or sender_email.split("@")[0],
                recipients=recipients,
                cc=cc,
                date=date,
                body=body,
                snippet=msg.get("snippet", ""),
                labels=labels,
                is_reply=headers.get("subject", "").lower().startswith("re:"),
                has_attachments=has_attachments,
            )

        except Exception as e:
            logger.error(f"Failed to parse message {message_id}: {e}")
            return None

    def _extract_body(self, payload: dict) -> str:
        """Extract text body from email payload (handles MIME structures)."""
        body = ""

        if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        elif payload.get("parts"):
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                    break
                elif part.get("parts"):
                    # Nested multipart
                    body = self._extract_body(part)
                    if body:
                        break

        # Clean up the body
        body = re.sub(r"<[^>]+>", "", body)  # Remove HTML tags
        body = re.sub(r"\n{3,}", "\n\n", body)  # Collapse newlines
        return body.strip()

    def _has_attachments(self, payload: dict) -> bool:
        """Check if email has attachments."""
        if payload.get("filename"):
            return True
        for part in payload.get("parts", []):
            if part.get("filename"):
                return True
            if self._has_attachments(part):
                return True
        return False

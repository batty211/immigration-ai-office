from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.config import settings
from app.models import GmailAccount, GmailWatch
from app.security import decrypt_refresh_token, encrypt_refresh_token

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailIntegrationError(RuntimeError):
    pass


class GmailConfigurationError(GmailIntegrationError):
    pass


@dataclass
class GmailMessage:
    id: str
    thread_id: str
    subject: str | None
    sender: str | None
    body: str
    attachments: list[dict[str, Any]]
    date: str | None
    snippet: str | None


class GmailService:
    def __init__(self, db: Session):
        self.db = db

    def ensure_configured(self) -> None:
        if not settings.google_oauth_configured:
            raise GmailConfigurationError(
                "Google OAuth is not configured. Set GOOGLE_CLIENT_ID, "
                "GOOGLE_CLIENT_SECRET, and GMAIL_TOKEN_ENCRYPTION_KEY."
            )

    def create_oauth_flow(self, state: str | None = None) -> Flow:
        self.ensure_configured()
        client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.gmail_callback_url],
            }
        }
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=GMAIL_SCOPES,
            state=state,
        )
        flow.redirect_uri = settings.gmail_callback_url
        return flow

    def get_authorization_url(self, state: str) -> str:
        flow = self.create_oauth_flow(state=state)
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return authorization_url

    def exchange_code(self, code: str, state: str) -> GmailAccount:
        flow = self.create_oauth_flow(state=state)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        if not credentials.refresh_token:
            raise GmailIntegrationError("Google did not return a refresh token")

        gmail = build("gmail", "v1", credentials=credentials, cache_discovery=False)
        profile = gmail.users().getProfile(userId="me").execute()
        email_address = profile["emailAddress"]
        history_id = profile.get("historyId")
        scopes = " ".join(credentials.scopes or GMAIL_SCOPES)
        encrypted_refresh_token = encrypt_refresh_token(credentials.refresh_token)

        account = (
            self.db.query(GmailAccount)
            .filter(GmailAccount.email_address == email_address)
            .one_or_none()
        )
        if account is None:
            account = GmailAccount(
                email_address=email_address,
                encrypted_refresh_token=encrypted_refresh_token,
                scopes=scopes,
                history_id=history_id,
                connected_at=datetime.now(UTC),
            )
            self.db.add(account)
        else:
            account.encrypted_refresh_token = encrypted_refresh_token
            account.scopes = scopes
            account.history_id = history_id
            account.connected_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(account)
        return account

    def get_connected_account(self) -> GmailAccount | None:
        return (
            self.db.query(GmailAccount)
            .order_by(GmailAccount.connected_at.desc())
            .first()
        )

    def get_status(self) -> dict[str, Any]:
        account = self.get_connected_account()
        if account is None:
            return {"connected": False, "email": None, "last_sync": None}

        return {
            "connected": True,
            "email": account.email_address,
            "last_sync": account.last_sync_at.isoformat() if account.last_sync_at else None,
        }

    def _build_credentials(self, account: GmailAccount) -> Credentials:
        credentials = Credentials(
            token=None,
            refresh_token=decrypt_refresh_token(account.encrypted_refresh_token),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=account.scopes.split(),
        )
        credentials.refresh(Request())
        return credentials

    def _build_gmail_client(self, account: GmailAccount):
        credentials = self._build_credentials(account)
        return build("gmail", "v1", credentials=credentials, cache_discovery=False)

    def start_watch(self) -> dict[str, Any]:
        self.ensure_configured()
        if not settings.gmail_pubsub_topic_name:
            raise GmailConfigurationError("GMAIL_PUBSUB_TOPIC_NAME is not configured")

        account = self.get_connected_account()
        if account is None:
            raise GmailIntegrationError("No Gmail account is connected")

        gmail = self._build_gmail_client(account)
        payload = {
            "topicName": settings.gmail_pubsub_topic_name,
            "labelIds": list(settings.gmail_watch_label_ids),
            "labelFilterBehavior": "include",
        }
        result = gmail.users().watch(userId="me", body=payload).execute()
        expiration_at = None
        expiration_ms = result.get("expiration")
        if expiration_ms:
            expiration_at = datetime.fromtimestamp(int(expiration_ms) / 1000, tz=UTC)

        watch = account.watch
        if watch is None:
            watch = GmailWatch(
                gmail_account_id=account.id,
                history_id=result["historyId"],
                expiration_at=expiration_at,
                topic_name=settings.gmail_pubsub_topic_name,
                status="active",
            )
            self.db.add(watch)
        else:
            watch.history_id = result["historyId"]
            watch.expiration_at = expiration_at
            watch.topic_name = settings.gmail_pubsub_topic_name
            watch.status = "active"

        account.history_id = result["historyId"]
        account.last_sync_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(account)

        return {
            "connected": True,
            "history_id": result["historyId"],
            "expiration": expiration_at.isoformat() if expiration_at else None,
        }

    def list_messages(self, max_results: int = 10) -> list[GmailMessage]:
        account = self.get_connected_account()
        if account is None:
            raise GmailIntegrationError("No Gmail account is connected")

        gmail = self._build_gmail_client(account)
        result = gmail.users().messages().list(userId="me", maxResults=max_results).execute()
        messages = result.get("messages", [])
        return [self.get_message(message["id"], gmail_client=gmail) for message in messages]

    def get_message(self, message_id: str, gmail_client=None) -> GmailMessage:
        account = self.get_connected_account()
        if account is None:
            raise GmailIntegrationError("No Gmail account is connected")

        gmail = gmail_client or self._build_gmail_client(account)
        response = (
            gmail.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        payload = response.get("payload", {})
        headers = {header["name"]: header["value"] for header in payload.get("headers", [])}
        body = self._extract_body(payload)
        attachments = self._extract_attachments(gmail, response)
        return GmailMessage(
            id=response["id"],
            thread_id=response["threadId"],
            subject=headers.get("Subject"),
            sender=headers.get("From"),
            body=body,
            attachments=attachments,
            date=self._normalize_date(headers.get("Date")),
            snippet=response.get("snippet"),
        )

    def _extract_body(self, payload: dict[str, Any]) -> str:
        parts = payload.get("parts") or []
        if not parts:
            return self._decode_body(payload.get("body", {}).get("data"))

        plain_parts = self._find_parts(parts, "text/plain")
        html_parts = self._find_parts(parts, "text/html")
        for part in plain_parts + html_parts:
            data = part.get("body", {}).get("data")
            if data:
                return self._decode_body(data)
        return ""

    def _find_parts(self, parts: list[dict[str, Any]], mime_type: str) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        for part in parts:
            if part.get("mimeType") == mime_type:
                found.append(part)
            nested_parts = part.get("parts") or []
            if nested_parts:
                found.extend(self._find_parts(nested_parts, mime_type))
        return found

    def _extract_attachments(self, gmail, message: dict[str, Any]) -> list[dict[str, Any]]:
        attachments: list[dict[str, Any]] = []

        def walk(parts: list[dict[str, Any]]) -> None:
            for part in parts:
                nested_parts = part.get("parts") or []
                if nested_parts:
                    walk(nested_parts)
                filename = part.get("filename")
                body = part.get("body", {})
                attachment_id = body.get("attachmentId")
                if filename and attachment_id:
                    attachment = (
                        gmail.users()
                        .messages()
                        .attachments()
                        .get(userId="me", messageId=message["id"], id=attachment_id)
                        .execute()
                    )
                    attachments.append(
                        {
                            "filename": filename,
                            "mime_type": part.get("mimeType"),
                            "size": body.get("size"),
                            "data": self._decode_body(attachment.get("data")),
                        }
                    )

        walk(message.get("payload", {}).get("parts") or [])
        return attachments

    def _decode_body(self, encoded_value: str | None) -> str:
        if not encoded_value:
            return ""
        padded = encoded_value + "=" * (-len(encoded_value) % 4)
        try:
            return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")
        except (binascii.Error, ValueError):
            return ""

    def _normalize_date(self, raw_date: str | None) -> str | None:
        if not raw_date:
            return None
        try:
            return parsedate_to_datetime(raw_date).astimezone(UTC).isoformat()
        except (TypeError, ValueError):
            return raw_date

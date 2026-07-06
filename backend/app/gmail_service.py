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
from googleapiclient.errors import HttpError
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import EmailMessage, GmailAccount, GmailWatch
from app.services.mail_officer import MailOfficerError, MailOfficerService
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
    recipients: str | None
    body: str
    attachments: list[dict[str, Any]]
    date: str | None
    snippet: str | None
    history_id: str | None
    label_ids: list[str]
    is_unread: bool


@dataclass
class SyncResult:
    stored: int
    processed: int
    history_id: str | None


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
            return {"connected": False, "email": None, "last_sync": None, "stored_messages": 0}

        stored_messages = (
            self.db.query(func.count(EmailMessage.id))
            .filter(EmailMessage.gmail_account_id == account.id)
            .scalar()
            or 0
        )

        return {
            "connected": True,
            "email": account.email_address,
            "last_sync": account.last_sync_at.isoformat() if account.last_sync_at else None,
            "stored_messages": stored_messages,
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
        initial_sync = self.sync_recent_messages(
            account=account,
            gmail_client=gmail,
            max_results=25,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(account)

        return {
            "connected": True,
            "history_id": result["historyId"],
            "expiration": expiration_at.isoformat() if expiration_at else None,
            "stored": initial_sync.stored,
            "processed": initial_sync.processed,
        }

    def list_messages(self, max_results: int = 10) -> list[GmailMessage]:
        account = self.get_connected_account()
        if account is None:
            raise GmailIntegrationError("No Gmail account is connected")

        gmail = self._build_gmail_client(account)
        result = gmail.users().messages().list(userId="me", maxResults=max_results).execute()
        messages = result.get("messages", [])
        return [self.get_message(message["id"], gmail_client=gmail, account=account) for message in messages]

    def get_message(
        self,
        message_id: str,
        gmail_client=None,
        account: GmailAccount | None = None,
    ) -> GmailMessage:
        gmail = gmail_client
        if gmail is None:
            active_account = account or self.get_connected_account()
            if active_account is None:
                raise GmailIntegrationError("No Gmail account is connected")
            gmail = self._build_gmail_client(active_account)
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
            recipients=headers.get("To"),
            body=body,
            attachments=attachments,
            date=self._normalize_date(headers.get("Date")),
            snippet=response.get("snippet"),
            history_id=response.get("historyId"),
            label_ids=response.get("labelIds", []),
            is_unread="UNREAD" in response.get("labelIds", []),
        )

    def sync_recent_messages(
        self,
        max_results: int = 25,
        account: GmailAccount | None = None,
        gmail_client=None,
        commit: bool = True,
    ) -> SyncResult:
        active_account = account or self.get_connected_account()
        if active_account is None:
            raise GmailIntegrationError("No Gmail account is connected")

        gmail = gmail_client or self._build_gmail_client(active_account)
        result = gmail.users().messages().list(userId="me", maxResults=max_results).execute()
        messages = result.get("messages", [])

        stored = 0
        processed = 0
        for message in messages:
            gmail_message = self.get_message(message["id"], gmail_client=gmail, account=active_account)
            email_record, was_created = self._upsert_email_message(active_account, gmail_message)
            stored += int(was_created)
            processed += int(email_record.processing_status == "processed")

        active_account.last_sync_at = datetime.now(UTC)
        if commit:
            self.db.commit()

        return SyncResult(stored=stored, processed=processed, history_id=active_account.history_id)

    def sync_history(self, history_id: str | None = None, account: GmailAccount | None = None) -> SyncResult:
        active_account = account or self.get_connected_account()
        if active_account is None:
            raise GmailIntegrationError("No Gmail account is connected")

        start_history_id = history_id or active_account.history_id
        if not start_history_id:
            return self.sync_recent_messages(account=active_account)

        gmail = self._build_gmail_client(active_account)
        message_ids: set[str] = set()
        next_page_token: str | None = None
        latest_history_id = start_history_id

        try:
            while True:
                request = (
                    gmail.users()
                    .history()
                    .list(
                        userId="me",
                        startHistoryId=start_history_id,
                        historyTypes=["messageAdded"],
                        pageToken=next_page_token,
                    )
                )
                response = request.execute()
                latest_history_id = response.get("historyId", latest_history_id)
                for history_item in response.get("history", []):
                    for added in history_item.get("messagesAdded", []):
                        message = added.get("message", {})
                        message_id = message.get("id")
                        if message_id:
                            message_ids.add(message_id)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
        except HttpError as error:
            if getattr(getattr(error, "resp", None), "status", None) == 404:
                return self.sync_recent_messages(account=active_account)
            raise

        stored = 0
        processed = 0
        for message_id in sorted(message_ids):
            gmail_message = self.get_message(message_id, gmail_client=gmail, account=active_account)
            email_record, was_created = self._upsert_email_message(active_account, gmail_message)
            stored += int(was_created)
            processed += int(email_record.processing_status == "processed")

        active_account.history_id = latest_history_id
        active_account.last_sync_at = datetime.now(UTC)
        self.db.commit()

        return SyncResult(stored=stored, processed=processed, history_id=latest_history_id)

    def handle_push_notification(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = payload.get("message") or {}
        encoded_data = message.get("data")
        if not encoded_data:
            raise GmailIntegrationError("Notification payload does not include message data")

        decoded_payload = self._decode_json_data(encoded_data)
        email_address = decoded_payload.get("emailAddress")
        history_id = decoded_payload.get("historyId")
        if not email_address or not history_id:
            raise GmailIntegrationError("Notification payload is missing emailAddress or historyId")

        account = (
            self.db.query(GmailAccount)
            .filter(GmailAccount.email_address == email_address)
            .one_or_none()
        )
        if account is None:
            raise GmailIntegrationError(f"No connected Gmail account found for {email_address}")

        result = self.sync_history(history_id=account.history_id or history_id, account=account)
        return {
            "ok": True,
            "email": email_address,
            "history_id": result.history_id,
            "stored": result.stored,
            "processed": result.processed,
        }

    def get_dashboard(self) -> dict[str, Any]:
        account = self.get_connected_account()
        if account is None:
            return {
                "connected": False,
                "email": None,
                "last_sync": None,
                "metrics": {
                    "stored": 0,
                    "processed": 0,
                    "unread": 0,
                },
                "messages": [],
            }

        metrics = self.db.query(
            func.count(EmailMessage.id),
            func.count(EmailMessage.id).filter(EmailMessage.processing_status == "processed"),
            func.count(EmailMessage.id).filter(EmailMessage.is_unread.is_(True)),
        ).filter(EmailMessage.gmail_account_id == account.id).one()

        messages = (
            self.db.query(EmailMessage)
            .filter(EmailMessage.gmail_account_id == account.id)
            .order_by(
                desc(EmailMessage.received_at),
                desc(EmailMessage.created_at),
            )
            .limit(25)
            .all()
        )

        return {
            "connected": True,
            "email": account.email_address,
            "last_sync": account.last_sync_at.isoformat() if account.last_sync_at else None,
            "metrics": {
                "stored": metrics[0] or 0,
                "processed": metrics[1] or 0,
                "unread": metrics[2] or 0,
            },
            "messages": [
                {
                    "id": message.id,
                    "gmail_message_id": message.gmail_message_id,
                    "subject": message.subject,
                    "sender": message.sender,
                    "recipients": message.recipients,
                    "snippet": message.snippet,
                    "body": message.body,
                    "received_at": message.received_at.isoformat() if message.received_at else None,
                    "processing_status": message.processing_status,
                    "attachments": message.attachments,
                    "is_unread": message.is_unread,
                    "analysis": (
                        {
                            "summary": message.analysis.summary,
                            "category": message.analysis.category,
                            "priority": message.analysis.priority,
                            "requires_action": message.analysis.requires_action,
                            "requires_reply": message.analysis.requires_reply,
                            "deadline": message.analysis.deadline,
                            "recommended_action": message.analysis.recommended_action,
                            "recommended_assignee": message.analysis.recommended_assignee,
                            "tags": message.analysis.tags,
                            "confidence": message.analysis.confidence,
                        }
                        if message.analysis
                        else None
                    ),
                }
                for message in messages
            ],
        }

    def _upsert_email_message(
        self,
        account: GmailAccount,
        gmail_message: GmailMessage,
    ) -> tuple[EmailMessage, bool]:
        email_record = (
            self.db.query(EmailMessage)
            .filter(EmailMessage.gmail_message_id == gmail_message.id)
            .one_or_none()
        )
        was_created = email_record is None

        if email_record is None:
            email_record = EmailMessage(
                gmail_account_id=account.id,
                gmail_message_id=gmail_message.id,
            )
            self.db.add(email_record)

        email_record.gmail_thread_id = gmail_message.thread_id
        email_record.gmail_history_id = gmail_message.history_id
        email_record.subject = gmail_message.subject
        email_record.sender = gmail_message.sender
        email_record.recipients = gmail_message.recipients
        email_record.snippet = gmail_message.snippet
        email_record.body = gmail_message.body
        email_record.attachments = gmail_message.attachments
        email_record.label_ids = gmail_message.label_ids
        email_record.received_at = self._parse_iso_datetime(gmail_message.date)
        email_record.is_unread = gmail_message.is_unread
        if email_record.id is None:
            self.db.flush()
        self._process_email_message(email_record)
        return email_record, was_created

    def _process_email_message(self, email_record: EmailMessage) -> None:
        email_record.processing_status = "processed"
        email_record.processed_at = datetime.now(UTC)
        if settings.openai_configured:
            try:
                MailOfficerService(self.db).analyze_email_message(email_record)
            except MailOfficerError:
                # Gmail ingestion should continue even if AI analysis is temporarily unavailable.
                pass

    def _parse_iso_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _decode_json_data(self, encoded_value: str) -> dict[str, Any]:
        raw_value = self._decode_body(encoded_value)
        if not raw_value:
            raise GmailIntegrationError("Notification payload could not be decoded")
        try:
            import json

            return json.loads(raw_value)
        except ValueError as error:
            raise GmailIntegrationError("Notification payload is not valid JSON") from error

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

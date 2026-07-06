from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

from sqlalchemy.orm import Session

from app.config import settings
from app.models import EmailAnalysis, EmailMessage

ALLOWED_CATEGORIES = [
    "official_order",
    "government_letter",
    "meeting",
    "document_request",
    "information_only",
    "immigration_case",
    "finance",
    "procurement",
    "personnel",
    "IT",
    "other",
]

ALLOWED_PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class MailOfficerError(RuntimeError):
    pass


class MailOfficerConfigurationError(MailOfficerError):
    pass


class MailOfficerAnalysisError(MailOfficerError):
    pass


@dataclass
class MailOfficerResult:
    summary: str
    category: str
    priority: str
    requires_action: bool
    requires_reply: bool
    deadline: str | None
    recommended_action: str
    recommended_assignee: str
    tags: list[str]
    confidence: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "category": self.category,
            "priority": self.priority,
            "requires_action": self.requires_action,
            "requires_reply": self.requires_reply,
            "deadline": self.deadline,
            "recommended_action": self.recommended_action,
            "recommended_assignee": self.recommended_assignee,
            "tags": self.tags,
            "confidence": self.confidence,
        }


class MailOfficerService:
    def __init__(self, db: Session):
        self.db = db
        self.prompt_path = Path(__file__).resolve().parents[2] / "prompts" / "mail_officer.md"

    def ensure_configured(self) -> None:
        if not settings.openai_configured:
            raise MailOfficerConfigurationError("OPENAI_API_KEY is not configured")

    def analyze_email_message(self, email_message: EmailMessage) -> EmailAnalysis:
        self.ensure_configured()
        result = self._request_analysis(email_message)

        analysis = email_message.analysis
        if analysis is None:
            analysis = EmailAnalysis(email_message_id=email_message.id)
            self.db.add(analysis)

        analysis.summary = result.summary
        analysis.category = result.category
        analysis.priority = result.priority
        analysis.requires_action = result.requires_action
        analysis.requires_reply = result.requires_reply
        analysis.deadline = result.deadline
        analysis.recommended_action = result.recommended_action
        analysis.recommended_assignee = result.recommended_assignee
        analysis.tags = result.tags
        analysis.confidence = result.confidence
        analysis.raw_result = result.as_dict()
        email_message.analysis = analysis
        return analysis

    def analyze_email_by_id(self, email_id: int) -> EmailAnalysis:
        email_message = self.db.get(EmailMessage, email_id)
        if email_message is None:
            raise MailOfficerAnalysisError(f"Email message {email_id} was not found")

        analysis = self.analyze_email_message(email_message)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_analysis_by_email_id(self, email_id: int) -> EmailAnalysis | None:
        email_message = self.db.get(EmailMessage, email_id)
        if email_message is None:
            raise MailOfficerAnalysisError(f"Email message {email_id} was not found")
        return email_message.analysis

    def analyze_pending(self) -> dict[str, int]:
        self.ensure_configured()
        pending_messages = (
            self.db.query(EmailMessage)
            .outerjoin(EmailAnalysis, EmailAnalysis.email_message_id == EmailMessage.id)
            .filter(EmailAnalysis.id.is_(None))
            .order_by(EmailMessage.received_at.asc(), EmailMessage.created_at.asc())
            .all()
        )

        analyzed = 0
        for email_message in pending_messages:
            self.analyze_email_message(email_message)
            analyzed += 1

        self.db.commit()
        return {"pending": len(pending_messages), "analyzed": analyzed}

    def serialize_analysis(self, analysis: EmailAnalysis) -> dict[str, Any]:
        return {
            "id": analysis.id,
            "email_message_id": analysis.email_message_id,
            "summary": analysis.summary,
            "category": analysis.category,
            "priority": analysis.priority,
            "requires_action": analysis.requires_action,
            "requires_reply": analysis.requires_reply,
            "deadline": analysis.deadline,
            "recommended_action": analysis.recommended_action,
            "recommended_assignee": analysis.recommended_assignee,
            "tags": analysis.tags,
            "confidence": analysis.confidence,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None,
        }

    def _request_analysis(self, email_message: EmailMessage) -> MailOfficerResult:
        prompt = self.prompt_path.read_text(encoding="utf-8")
        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": self._build_email_payload(email_message)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "mail_officer_analysis",
                    "strict": True,
                    "schema": self._analysis_schema(),
                },
            },
        }

        endpoint = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        http_request = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=settings.openai_timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise MailOfficerAnalysisError(f"OpenAI request failed: {exc.code} {detail}") from exc
        except error.URLError as exc:
            raise MailOfficerAnalysisError(f"OpenAI request failed: {exc.reason}") from exc

        try:
            completion = json.loads(response_body)
            choice = completion["choices"][0]
            message = choice["message"]
            refusal = message.get("refusal")
            if refusal:
                raise MailOfficerAnalysisError(f"Model refused analysis: {refusal}")

            content = message.get("content")
            if isinstance(content, str):
                parsed = json.loads(content)
            elif isinstance(content, list):
                text_chunks = [
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                ]
                parsed = json.loads("".join(text_chunks))
            else:
                raise MailOfficerAnalysisError("Model response did not include JSON content")
        except (KeyError, ValueError, TypeError) as exc:
            raise MailOfficerAnalysisError(f"Unable to parse Mail Officer response: {exc}") from exc

        return self._normalize_result(parsed)

    def _build_email_payload(self, email_message: EmailMessage) -> str:
        attachments = email_message.attachments or []
        return json.dumps(
            {
                "message_id": email_message.id,
                "subject": email_message.subject,
                "sender": email_message.sender,
                "recipients": email_message.recipients,
                "received_at": email_message.received_at.isoformat() if email_message.received_at else None,
                "snippet": email_message.snippet,
                "body": email_message.body,
                "attachments": attachments,
                "labels": email_message.label_ids or [],
            },
            ensure_ascii=False,
        )

    def _normalize_result(self, payload: dict[str, Any]) -> MailOfficerResult:
        category = str(payload.get("category", "other"))
        if category not in ALLOWED_CATEGORIES:
            category = "other"

        priority = str(payload.get("priority", "LOW")).upper()
        if priority not in ALLOWED_PRIORITIES:
            priority = "LOW"

        tags = payload.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        deadline = payload.get("deadline")
        if deadline is not None:
            deadline = str(deadline).strip() or None

        confidence = payload.get("confidence", 0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        return MailOfficerResult(
            summary=str(payload.get("summary", "")).strip(),
            category=category,
            priority=priority,
            requires_action=bool(payload.get("requires_action", False)),
            requires_reply=bool(payload.get("requires_reply", False)),
            deadline=deadline,
            recommended_action=str(payload.get("recommended_action", "")).strip(),
            recommended_assignee=str(payload.get("recommended_assignee", "")).strip(),
            tags=[str(tag).strip() for tag in tags if str(tag).strip()],
            confidence=confidence,
        )

    def _analysis_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "category": {"type": "string", "enum": ALLOWED_CATEGORIES},
                "priority": {"type": "string", "enum": ALLOWED_PRIORITIES},
                "requires_action": {"type": "boolean"},
                "requires_reply": {"type": "boolean"},
                "deadline": {"type": ["string", "null"]},
                "recommended_action": {"type": "string"},
                "recommended_assignee": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number"},
            },
            "required": [
                "summary",
                "category",
                "priority",
                "requires_action",
                "requires_reply",
                "deadline",
                "recommended_action",
                "recommended_assignee",
                "tags",
                "confidence",
            ],
            "additionalProperties": False,
        }

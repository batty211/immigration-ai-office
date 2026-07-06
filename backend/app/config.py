from __future__ import annotations

import os
from dataclasses import dataclass


def _build_database_url() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "immigration_ai_office")
    username = os.getenv("POSTGRES_USER", "immigration")
    password = os.getenv("POSTGRES_PASSWORD", "immigration")
    return f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"


@dataclass(frozen=True)
class Settings:
    app_base_url: str = os.getenv("APP_BASE_URL", "http://localhost")
    frontend_base_url: str = os.getenv("FRONTEND_BASE_URL", "http://localhost")
    database_url: str = _build_database_url()
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    gmail_oauth_redirect_path: str = os.getenv("GMAIL_OAUTH_REDIRECT_PATH", "/gmail/callback")
    gmail_token_encryption_key: str = os.getenv("GMAIL_TOKEN_ENCRYPTION_KEY", "")
    gmail_pubsub_topic_name: str = os.getenv("GMAIL_PUBSUB_TOPIC_NAME", "")
    gmail_watch_label_ids: tuple[str, ...] = tuple(
        label.strip()
        for label in os.getenv("GMAIL_WATCH_LABEL_IDS", "INBOX").split(",")
        if label.strip()
    )

    @property
    def gmail_callback_url(self) -> str:
        return f"{self.app_base_url.rstrip('/')}{self.gmail_oauth_redirect_path}"

    @property
    def google_oauth_configured(self) -> bool:
        return bool(
            self.google_client_id
            and self.google_client_secret
            and self.gmail_token_encryption_key
        )


settings = Settings()

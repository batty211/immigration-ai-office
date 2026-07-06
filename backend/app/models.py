from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class GmailAccount(Base):
    __tablename__ = "gmail_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text())
    scopes: Mapped[str] = mapped_column(Text())
    history_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    watch: Mapped["GmailWatch | None"] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        uselist=False,
    )
    email_messages: Mapped[list["EmailMessage"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )


class GmailWatch(Base):
    __tablename__ = "gmail_watch"

    id: Mapped[int] = mapped_column(primary_key=True)
    gmail_account_id: Mapped[int] = mapped_column(ForeignKey("gmail_accounts.id"), unique=True, index=True)
    history_id: Mapped[str] = mapped_column(String(255))
    expiration_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    topic_name: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped[GmailAccount] = relationship(back_populates="watch")


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    gmail_account_id: Mapped[int] = mapped_column(ForeignKey("gmail_accounts.id"), index=True)
    gmail_message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    gmail_thread_id: Mapped[str] = mapped_column(String(255), index=True)
    gmail_history_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(Text(), nullable=True)
    sender: Mapped[str | None] = mapped_column(Text(), nullable=True)
    recipients: Mapped[str | None] = mapped_column(Text(), nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text(), nullable=True)
    body: Mapped[str] = mapped_column(Text(), default="")
    attachments: Mapped[list[dict]] = mapped_column(JSON, default=list)
    label_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="processed", index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_unread: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped[GmailAccount] = relationship(back_populates="email_messages")
    analysis: Mapped["EmailAnalysis | None"] = relationship(
        back_populates="email_message",
        cascade="all, delete-orphan",
        uselist=False,
    )


class EmailAnalysis(Base):
    __tablename__ = "email_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_message_id: Mapped[int] = mapped_column(ForeignKey("email_messages.id"), unique=True, index=True)
    summary: Mapped[str] = mapped_column(Text())
    category: Mapped[str] = mapped_column(String(100), index=True)
    priority: Mapped[str] = mapped_column(String(20), index=True)
    requires_action: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_reply: Mapped[bool] = mapped_column(Boolean, default=False)
    deadline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recommended_action: Mapped[str] = mapped_column(Text())
    recommended_assignee: Mapped[str] = mapped_column(Text())
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(default=0.0)
    raw_result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    email_message: Mapped[EmailMessage] = relationship(back_populates="analysis")

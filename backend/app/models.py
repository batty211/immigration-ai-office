from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
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

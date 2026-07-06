from __future__ import annotations

from cryptography.fernet import Fernet

from app.config import settings


class EncryptionNotConfiguredError(RuntimeError):
    pass


def _get_fernet() -> Fernet:
    if not settings.gmail_token_encryption_key:
        raise EncryptionNotConfiguredError("GMAIL_TOKEN_ENCRYPTION_KEY is not configured")
    return Fernet(settings.gmail_token_encryption_key.encode("utf-8"))


def encrypt_refresh_token(refresh_token: str) -> str:
    return _get_fernet().encrypt(refresh_token.encode("utf-8")).decode("utf-8")


def decrypt_refresh_token(encrypted_refresh_token: str) -> str:
    return _get_fernet().decrypt(encrypted_refresh_token.encode("utf-8")).decode("utf-8")

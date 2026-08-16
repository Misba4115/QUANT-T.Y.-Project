"""Application-level encryption for provider credentials and retained files."""
from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from core.config import get_settings


class SecretDecryptionError(RuntimeError):
    pass


class SecretBox:
    def __init__(self, key: str | None = None):
        settings = get_settings()
        configured = key or settings.credential_encryption_key
        if configured:
            material = configured.encode("utf-8")
            try:
                Fernet(material)
                self._key = material
            except (ValueError, TypeError):
                self._key = base64.urlsafe_b64encode(hashlib.sha256(material).digest())
        else:
            if settings.quant_env == "production":
                raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY is required in production")
            seed = f"quant-dev-only:{settings.jwt_secret_key}".encode("utf-8")
            self._key = base64.urlsafe_b64encode(hashlib.sha256(seed).digest())
        self._fernet = Fernet(self._key)

    def encrypt_json(self, value: dict[str, Any]) -> str:
        encoded = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return self._fernet.encrypt(encoded).decode("ascii")

    def decrypt_json(self, token: str) -> dict[str, Any]:
        try:
            value = json.loads(self._fernet.decrypt(token.encode("ascii")))
        except (InvalidToken, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise SecretDecryptionError("Stored credential could not be decrypted") from exc
        if not isinstance(value, dict):
            raise SecretDecryptionError("Stored credential has an invalid shape")
        return value

    def encrypt_bytes(self, value: bytes) -> bytes:
        return self._fernet.encrypt(value)

    def decrypt_bytes(self, value: bytes) -> bytes:
        try:
            return self._fernet.decrypt(value)
        except InvalidToken as exc:
            raise SecretDecryptionError("Stored file could not be decrypted") from exc

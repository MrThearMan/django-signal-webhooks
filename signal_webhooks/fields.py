from __future__ import annotations

import logging
from base64 import b64decode, b64encode
from os import urandom
from typing import TYPE_CHECKING

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.core.exceptions import ValidationError
from django.db import models

from .utils import decode_cipher_key

if TYPE_CHECKING:
    from .typing import Any

__all__ = [
    "TokenField",
]


logger = logging.getLogger(__name__)


class TokenField(models.CharField):
    """Encrypt token with a cipher before saving it."""

    def from_db_value(self, value: str, *args: Any, **kwargs: Any) -> str:  # noqa: ARG002
        if not value:
            return value

        key = decode_cipher_key()

        string = b64decode(value)
        nonce = string[:12]
        data = string[12:]
        cipher = AESGCM(key=key)

        try:
            decrypted_token = cipher.decrypt(nonce, data, None)
        except InvalidTag as error:
            msg = "Wrong cipher key."
            raise ValidationError(msg) from error

        return decrypted_token.decode()

    def get_prep_value(self, value: str, *args: Any, **kwargs: Any) -> str:  # noqa: ARG002
        if not value:
            return value

        key = decode_cipher_key()

        nonce = urandom(12)
        cipher = AESGCM(key)
        encrypted_token = cipher.encrypt(nonce, value.encode(encoding="utf-8"), None)
        return b64encode(nonce + encrypted_token).decode()

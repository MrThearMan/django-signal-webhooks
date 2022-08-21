import logging
from base64 import b64decode, b64encode
from os import urandom

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.core.exceptions import ValidationError
from django.db import models

from .utils import decode_cipher_key


__all__ = [
    "TokenField",
]


logger = logging.getLogger(__name__)


class TokenField(models.CharField):
    """Encrypt token with a cipher before saving it."""

    def from_db_value(self, value: str, *args, **kwargs) -> str:
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
            raise ValidationError("Wrong cipher key.") from error

        return decrypted_token.decode()

    def get_prep_value(self, value: str, *args, **kwargs) -> str:
        if not value:
            return value

        key = decode_cipher_key()

        nonce = urandom(12)
        cipher = AESGCM(key)
        encrypted_token = cipher.encrypt(nonce, value.encode(encoding="utf-8"), None)
        encoded_token = b64encode(nonce + encrypted_token).decode()
        return encoded_token

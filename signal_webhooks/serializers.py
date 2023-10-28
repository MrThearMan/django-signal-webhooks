from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.core.serializers import python

if TYPE_CHECKING:
    from django.db import models

__all__ = [
    "webhook_serializer",
]


logger = logging.getLogger(__name__)


class _WebhookSerializer(python.Serializer):
    """Custom serializer to skip m2m fields when serializing models post-delete."""

    def handle_m2m_field(self, obj: models.Model, field: models.Field) -> None:
        try:
            super().handle_m2m_field(obj, field)
        except Exception as error:  # noqa: BLE001 pragma: no cover
            logger.debug(f"Skip {field.name!r} during post-delete signal.", exc_info=error)
            self._current[field.name] = []

    def end_serialization(self) -> None:
        # Convert any non-serializable objects to strings
        self.objects = json.loads(json.dumps(self.objects[0], default=str))


webhook_serializer = _WebhookSerializer()

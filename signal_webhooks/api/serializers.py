from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from signal_webhooks.utils import get_webhook_model

if TYPE_CHECKING:
    from signal_webhooks.typing import Any

__all__ = [
    "WebhookSerializer",
]


class WebhookSerializer(ModelSerializer):
    class Meta:
        model = get_webhook_model()
        fields = [
            "id",
            "name",
            "signal",
            "ref",
            "endpoint",
            "headers",
            "auth_token",
            "enabled",
            "keep_last_response",
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if get_webhook_model().objects.filter(ref=attrs["ref"], endpoint=attrs["endpoint"]).exists():
            msg = "Webhook for this model to this endpoint already exists."  # pragma: no cover
            raise ValidationError(msg)  # pragma: no cover

        return attrs

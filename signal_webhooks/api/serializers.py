from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from ..typing import Any, Dict
from ..utils import get_webhookhook_model

__all__ = [
    "WebhookSerializer",
]


class WebhookSerializer(ModelSerializer):
    class Meta:
        model = get_webhookhook_model()
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

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if get_webhookhook_model().objects.filter(ref=attrs["ref"], endpoint=attrs["endpoint"]).exists():
            msg = "Webhook for this model to this endpoint already exists."
            raise ValidationError(msg)

        return attrs

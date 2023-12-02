from rest_framework.viewsets import ModelViewSet

from ..utils import get_webhook_model
from .serializers import WebhookSerializer

__all__ = [
    "WebhooksViewSet",
]


class WebhooksViewSet(ModelViewSet):
    serializer_class = WebhookSerializer
    queryset = get_webhook_model().objects.all()

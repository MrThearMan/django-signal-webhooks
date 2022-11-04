from django.db import models

from signal_webhooks.models import WebhookBase
from signal_webhooks.typing import ClientMethodKwargs


__all__ = [
    "MyModel",
    "MyWebhook",
]


class MyModel(models.Model):
    """Testing model."""

    name = models.CharField(max_length=256)

    def webhook_data(self):
        return {"fizz": "buzz"}


class TestModel(models.Model):
    """Testing model."""

    name = models.CharField(max_length=256)


class MyWebhook(WebhookBase):
    """Custom webhooks."""

    code = models.CharField(max_length=256)

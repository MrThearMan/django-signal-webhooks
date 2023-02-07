from django.db import models

from signal_webhooks.models import WebhookBase

__all__ = [
    "MyModel",
    "MyWebhook",
]


def webhook_function():
    return {"fizz": "buzz"}


class MyModel(models.Model):
    """Testing model."""

    name = models.CharField(max_length=256)

    def webhook_data(self):
        return webhook_function()


class TestModel(models.Model):
    """Testing model."""

    name = models.CharField(max_length=256)


class MyWebhook(WebhookBase):
    """Custom webhooks."""

    code = models.CharField(max_length=256)

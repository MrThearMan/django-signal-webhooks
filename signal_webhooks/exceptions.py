__all__ = [
    "WebhookCancelled",
]


class WebhookCancelled(Exception):
    """Webhook was cancelled before it was sent."""

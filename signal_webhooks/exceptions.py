__all__ = [
    "WebhookCancelled",
]


class WebhookCancelled(Exception):  # noqa: N818
    """Webhook was cancelled before it was sent."""

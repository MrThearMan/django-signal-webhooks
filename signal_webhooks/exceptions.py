from __future__ import annotations

__all__ = [
    "WebhookCancelled",
]


class WebhookCancelled(Exception):  # noqa: N818
    """Webhook was cancelled before it was sent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from .fields import TokenField
from .settings import webhook_settings
from .typing import MAX_COL_SIZE, METHOD_SIGNALS, SignalChoices
from .utils import decode_cipher_key, is_dict, model_from_reference, reference_for_model

if TYPE_CHECKING:
    from datetime import datetime

    from django.db.models import Model

    from .typing import Any, Dict, Method, Optional


__all__ = [
    "Webhook",
    "WebhookBase",
]


class WebhookQuerySet(models.QuerySet["Webhook"]):
    """Webhook queryset."""

    def get_for_model(self, instance: Model, method: Method) -> models.QuerySet[Webhook]:
        kwargs: Dict[str, Any] = webhook_settings.FILTER_KWARGS(instance, method)
        return self.filter(
            ref=reference_for_model(type(instance)),
            signal__in=METHOD_SIGNALS[method],
            enabled=True,
            **kwargs,
        )


class WebhookBase(models.Model):
    """Base webhook stuff."""

    name: str = models.CharField(
        unique=True,
        db_index=True,
        max_length=256,
        verbose_name="name",
        help_text="Webhook name.",
    )
    signal: SignalChoices = models.IntegerField(
        verbose_name="signal",
        help_text="Signal the webhook fires to.",
        choices=SignalChoices.choices,
    )
    ref: str = models.CharField(
        max_length=1024,
        db_index=True,
        verbose_name="referenced model",
        help_text="Dot import notation to the model the webhook is for.",
        validators=[model_from_reference],
    )
    endpoint: str = models.URLField(
        max_length=2048,
        verbose_name="endpoint",
        help_text="Target endpoint for this webhook.",
    )
    headers: Dict[str, Any] = models.JSONField(
        blank=True,
        default=dict,
        verbose_name="headers",
        help_text="Headers to send with the webhook request.",
        validators=[is_dict],
    )
    auth_token: str = TokenField(
        default="",
        blank=True,
        max_length=MAX_COL_SIZE,
        verbose_name="authentication token",
        help_text="Authentication token to use in an Authorization header.",
        validators=[decode_cipher_key],
    )
    enabled: bool = models.BooleanField(
        default=True,
        verbose_name="enabled",
        help_text="Is this webhook enabled?",
    )
    keep_last_response: bool = models.BooleanField(
        default=False,
        verbose_name="keep last response",
        help_text="Should the webhook keep a log of the latest response it got?",
    )
    created: datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name="created",
        help_text="When the webhook was created.",
    )
    updated: datetime = models.DateTimeField(
        auto_now=True,
        verbose_name="updated",
        help_text="When the webhook was last updated.",
    )
    last_response: str = models.CharField(
        default="",
        blank=True,
        max_length=MAX_COL_SIZE,
        verbose_name="last response",
        help_text="Latest response to this webhook.",
    )
    last_success: Optional[datetime] = models.DateTimeField(
        null=True,
        default=None,
        verbose_name="last success",
        help_text="When the webhook last succeeded.",
    )
    last_failure: Optional[datetime] = models.DateTimeField(
        null=True,
        default=None,
        verbose_name="last failure",
        help_text="When the webhook last failed.",
    )

    objects = WebhookQuerySet.as_manager()

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["ref", "endpoint"],
                name="prevent_duplicate_hooks_%(app_label)s_%(class)s",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def default_headers(self) -> Dict[str, str]:
        headers = self.headers.copy()
        headers.setdefault("Content-Type", "application/json")
        if self.auth_token:
            headers.setdefault("Authorization", self.auth_token)

        return headers


class Webhook(WebhookBase):
    """Saved webhooks."""

    class Meta(WebhookBase.Meta):
        swappable = "SIGNAL_WEBHOOKS_CUSTOM_MODEL"

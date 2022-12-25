from django.apps import AppConfig

__all__ = [
    "DjangoSignalWebhooksConfig",
]


class DjangoSignalWebhooksConfig(AppConfig):
    name = "signal_webhooks"
    verbose_name = "Django Signal Webhooks"
    default_auto_field = "django.db.models.BigAutoField"

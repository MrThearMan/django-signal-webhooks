# Generated by Django 4.1 on 2022-08-21 20:06

from django.db import migrations, models

import signal_webhooks.fields
import signal_webhooks.utils


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Webhook",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_index=True,
                        help_text="Webhook name.",
                        max_length=256,
                        unique=True,
                        verbose_name="name",
                    ),
                ),
                (
                    "signal",
                    models.IntegerField(
                        choices=[
                            (0, "CREATE"),
                            (1, "UPDATE"),
                            (2, "DELETE"),
                            (3, "CREATE OR UPDATE"),
                            (4, "CREATE OR DELETE"),
                            (5, "UPDATE OR DELETE"),
                            (6, "ALL"),
                        ],
                        help_text="Signal the webhook fires to.",
                        verbose_name="signal",
                    ),
                ),
                (
                    "ref",
                    models.CharField(
                        db_index=True,
                        help_text="Dot import notation to the model the webhook is for.",
                        max_length=1024,
                        validators=[signal_webhooks.utils.model_from_reference],
                        verbose_name="referenced model",
                    ),
                ),
                (
                    "endpoint",
                    models.URLField(
                        help_text="Target endpoint for this webhook.",
                        max_length=2048,
                        verbose_name="endpoint",
                    ),
                ),
                (
                    "headers",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Headers to send with the webhook request.",
                        validators=[signal_webhooks.utils.is_dict],
                        verbose_name="headers",
                    ),
                ),
                (
                    "auth_token",
                    signal_webhooks.fields.TokenField(
                        blank=True,
                        default="",
                        help_text="Authentication token to use in an Authorization header.",
                        max_length=8000,
                        validators=[signal_webhooks.utils.decode_cipher_key],
                        verbose_name="authentication token",
                    ),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=True,
                        help_text="Is this webhook enabled?",
                        verbose_name="enabled",
                    ),
                ),
                (
                    "keep_last_response",
                    models.BooleanField(
                        default=False,
                        help_text="Should the webhook keep a log of the latest response it got?",
                        verbose_name="keep last response",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="When the webhook was created.",
                        verbose_name="created",
                    ),
                ),
                (
                    "updated",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="When the webhook was last updated.",
                        verbose_name="updated",
                    ),
                ),
                (
                    "last_response",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Latest response to this webhook.",
                        max_length=8000,
                        verbose_name="last response",
                    ),
                ),
                (
                    "last_success",
                    models.DateTimeField(
                        default=None,
                        help_text="When the webhook last succeeded.",
                        null=True,
                        verbose_name="last success",
                    ),
                ),
                (
                    "last_failure",
                    models.DateTimeField(
                        default=None,
                        help_text="When the webhook last failed.",
                        null=True,
                        verbose_name="last failure",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "swappable": "SIGNAL_WEBHOOKS_CUSTOM_MODEL",
            },
        ),
        migrations.AddConstraint(
            model_name="webhook",
            constraint=models.UniqueConstraint(
                fields=("ref", "endpoint"),
                name="prevent_duplicate_hooks_signal_webhooks_webhook",
            ),
        ),
    ]

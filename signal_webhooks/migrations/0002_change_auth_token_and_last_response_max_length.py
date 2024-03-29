# Generated by Django 4.2.6 on 2023-11-25 08:58

from django.db import migrations, models

import signal_webhooks.fields
import signal_webhooks.utils


class Migration(migrations.Migration):
    dependencies = [
        ("signal_webhooks", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="webhook",
            name="auth_token",
            field=signal_webhooks.fields.TokenField(
                blank=True,
                default="",
                help_text="Authentication token to use in an Authorization header.",
                max_length=8000,
                validators=[signal_webhooks.utils.decode_cipher_key],
                verbose_name="authentication token",
            ),
        ),
        migrations.AlterField(
            model_name="webhook",
            name="last_response",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Latest response to this webhook.",
                max_length=8000,
                verbose_name="last response",
            ),
        ),
    ]

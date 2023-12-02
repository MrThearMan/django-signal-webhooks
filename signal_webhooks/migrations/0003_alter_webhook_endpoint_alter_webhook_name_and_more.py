# Generated by Django 4.2.6 on 2023-12-02 11:01

from django.db import migrations, models

import signal_webhooks.utils


class Migration(migrations.Migration):
    dependencies = [
        ("signal_webhooks", "0002_change_auth_token_and_last_response_max_length"),
    ]

    operations = [
        migrations.AlterField(
            model_name="webhook",
            name="endpoint",
            field=models.URLField(
                help_text="Target endpoint for this webhook.",
                max_length=2047,
                verbose_name="endpoint",
            ),
        ),
        migrations.AlterField(
            model_name="webhook",
            name="name",
            field=models.CharField(
                db_index=True,
                help_text="Webhook name.",
                max_length=255,
                unique=True,
                verbose_name="name",
            ),
        ),
        migrations.AlterField(
            model_name="webhook",
            name="ref",
            field=models.CharField(
                db_index=True,
                help_text="Dot import notation to the model the webhook is for.",
                max_length=1023,
                validators=[signal_webhooks.utils.model_from_reference],
                verbose_name="referenced model",
            ),
        ),
        migrations.AlterField(
            model_name="webhook",
            name="signal",
            field=models.CharField(
                choices=[
                    ("CREATE", "Create"),
                    ("UPDATE", "Update"),
                    ("DELETE", "Delete"),
                    ("M2M", "M2M changed"),
                    ("CREATE_OR_UPDATE", "Create or Update"),
                    ("CREATE_OR_DELETE", "Create or Delete"),
                    ("CREATE_OR_M2M", "Create or M2M changed"),
                    ("UPDATE_OR_DELETE", "Update or Delete"),
                    ("UPDATE_OR_M2M", "Update or M2M changed"),
                    ("DELETE_OR_M2M", "Delete or M2M changed"),
                    ("CREATE_UPDATE_OR_DELETE", "Create, Update or Delete"),
                    ("CREATE_UPDATE_OR_M2M", "Create, Update or M2M changed"),
                    ("CREATE_DELETE_OR_M2M", "Create, Delete or M2M changed"),
                    ("UPDATE_DELETE_OR_M2M", "Update, Delete or M2M changed"),
                    ("CREATE_UPDATE_DELETE_OR_M2M", "Create, Update or Delete, or M2M changed"),
                ],
                help_text="Signal the webhook fires to.",
                max_length=255,
                verbose_name="signal",
            ),
        ),
    ]

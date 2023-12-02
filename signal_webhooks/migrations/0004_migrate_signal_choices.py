# ruff: noqa

from django.db import migrations, models

migrations_mapping = {
    0: "CREATE",
    1: "UPDATE",
    2: "DELETE",
    3: "CREATE_OR_UPDATE",
    4: "CREATE_OR_DELETE",
    5: "UPDATE_OR_DELETE",
    6: "CREATE_UPDATE_OR_DELETE",
}


def migrate_signal_choices(apps, schema_editor):  # pragma: no cover
    # Migrate the signal choices from ints to strings.
    Webhook = apps.get_model("signal_webhooks", "Webhook")
    Webhook.objects.update(
        signal=models.Case(
            *(models.When(models.Q(signal=i), then=models.Value(signal)) for i, signal in migrations_mapping.items()),
            default=models.Value("CREATE_UPDATE_OR_DELETE"),
        ),
    )


def reverse_migrate_signal_choices(apps, schema_editor):  # pragma: no cover
    # Reverse the signal migration.
    Webhook = apps.get_model("signal_webhooks", "Webhook")
    Webhook.objects.update(
        signal=models.Case(
            *(models.When(models.Q(signal=signal), then=models.Value(i)) for i, signal in migrations_mapping.items()),
            default=models.Value(6),  # "ALL"
        ),
        # Disable all webhooks that are not in the new signal choices.
        enabled=models.Case(
            models.When(models.Q(signal__in=list(migrations_mapping.values())), then=models.Value(True)),
            default=models.Value(False),
        ),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("signal_webhooks", "0003_alter_webhook_endpoint_alter_webhook_name_and_more"),
    ]

    operations = [
        migrations.RunPython(
            code=migrate_signal_choices,
            reverse_code=reverse_migrate_signal_choices,
        )
    ]

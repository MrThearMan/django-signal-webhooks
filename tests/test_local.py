from os import getenv

import pytest

from signal_webhooks.models import Webhook
from signal_webhooks.typing import SignalChoices
from tests.my_app.models import MyModel


@pytest.mark.e2e
@pytest.mark.skipif(getenv("CI", "false") == "true", reason="Only for testing locally")
@pytest.mark.django_db(transaction=True)
def test_webhook_e2e__single_webhook__ngrok(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "TIMEOUT": 10,
        "HOOKS": {
            "tests.my_app.models.MyModel": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
        ref="tests.my_app.models.MyModel",
        endpoint="https://1cc2-194-137-1-169.eu.ngrok.io" + "/hook/",
    )

    user = MyModel(name="x")
    user.save()


@pytest.mark.e2e
@pytest.mark.skipif(getenv("CI", "false") == "true", reason="Only for testing locally")
@pytest.mark.django_db(transaction=True)
def test_webhook_e2e__single_webhook__timeout(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "TIMEOUT": 1,
        "HOOKS": {
            "tests.my_app.models.MyModel": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
        ref="tests.my_app.models.MyModel",
        endpoint="https://httpstat.us/400?sleep=5000",
    )

    user = MyModel(name="x")
    user.save()

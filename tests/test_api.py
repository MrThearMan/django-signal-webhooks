from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from signal_webhooks.models import Webhook
from signal_webhooks.typing import SignalChoices

pytestmark = [
    pytest.mark.django_db,
]


def test_webhook_api(settings, api_client: APIClient):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M.value,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "https://www.example.com",
        "headers": {},
        "auth_token": "",
        "enabled": True,
        "keep_last_response": False,
    }

    response = api_client.post(reverse("webhook-list"), data=data, format="json")

    assert response.json() == {
        "id": 1,
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M.value,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "https://www.example.com",
        "headers": {},
        "auth_token": "",
        "enabled": True,
        "keep_last_response": False,
    }

    user = User(
        username="user",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_1:
        user.save()

    mock_1.assert_called_once()


def test_webhook_api__exists(settings, api_client: APIClient):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M.value,
        ref="django.contrib.auth.models.User",
        endpoint="https://www.example.com",
        headers={},
        auth_token="",
        enabled=True,
        keep_last_response=False,
    )

    data = {
        "name": "bar",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M.value,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "https://www.example.com",
        "headers": {},
        "auth_token": "",
        "enabled": True,
        "keep_last_response": False,
    }

    response = api_client.post(reverse("webhook-list"), data=data, format="json")

    assert response.json() == {"non_field_errors": ["Webhook for this model to this endpoint already exists."]}

import asyncio
import re
from time import sleep
from unittest.mock import AsyncMock, patch

import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ImproperlyConfigured, ValidationError
from httpx import Response

from signal_webhooks.exceptions import WebhookCancelled
from signal_webhooks.models import Webhook
from signal_webhooks.typing import SignalChoices
from signal_webhooks.utils import get_webhook_model
from tests.my_app.models import MyModel, MyWebhook

pytestmark = [
    pytest.mark.django_db(transaction=True),
]


def test_webhook__default_setup(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_1:
        user.save()

    mock_1.assert_called_once()

    group = Group.objects.create(name="x")
    with patch("signal_webhooks.handlers.default_hook_handler") as mock_2:
        user.groups.add(group)

    mock_2.assert_called_once()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_3:
        user.groups.remove(group)

    mock_3.assert_called_once()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_4:
        user.groups.clear()

    mock_4.assert_called_once()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_5:
        user.save(update_fields=["username"])

    mock_5.assert_called_once()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_6:
        user.delete()

    mock_6.assert_called_once()


def test_webhook__default_setup__different_model(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.Group": ...,
        },
    }

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_1:
        user.save()

    mock_1.assert_not_called()

    group = Group.objects.create(name="x")
    with patch("signal_webhooks.handlers.default_hook_handler") as mock_2:
        user.groups.add(group)

    mock_2.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_3:
        user.groups.remove(group)

    mock_3.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_4:
        user.groups.clear()

    mock_4.assert_not_called()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_5:
        user.save(update_fields=["username"])

    mock_5.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_6:
        user.delete()

    mock_6.assert_not_called()


def test_webhook__default_setup__explicit_deny(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": None,
        },
    }

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_1:
        user.save()

    mock_1.assert_not_called()

    group = Group.objects.create(name="x")
    with patch("signal_webhooks.handlers.default_hook_handler") as mock_2:
        user.groups.add(group)

    mock_2.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_3:
        user.groups.remove(group)

    mock_3.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_4:
        user.groups.clear()

    mock_4.assert_not_called()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_5:
        user.save(update_fields=["username"])

    mock_5.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_6:
        user.delete()

    mock_6.assert_not_called()


def test_webhook__default_setup__for_methods(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "CREATE": ...,
                "UPDATE": ...,
                "DELETE": ...,
                "M2M_ADD": ...,
                "M2M_REMOVE": ...,
                "M2M_CLEAR": ...,
            },
        },
    }

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_1:
        user.save()

    mock_1.assert_called_once()

    group = Group.objects.create(name="x")
    with patch("signal_webhooks.handlers.default_hook_handler") as mock_2:
        user.groups.add(group)

    mock_2.assert_called_once()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_3:
        user.groups.remove(group)

    mock_3.assert_called_once()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_4:
        user.groups.clear()

    mock_4.assert_called_once()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_5:
        user.save(update_fields=["username"])

    mock_5.assert_called_once()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_6:
        user.delete()

    mock_6.assert_called_once()


def test_webhook__default_setup__for_methods__not_defined(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {},
        },
    }

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_1:
        user.save()

    mock_1.assert_not_called()

    group = Group.objects.create(name="x")
    with patch("signal_webhooks.handlers.default_hook_handler") as mock_2:
        user.groups.add(group)

    mock_2.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_3:
        user.groups.remove(group)

    mock_3.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_4:
        user.groups.clear()

    mock_4.assert_not_called()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_5:
        user.save(update_fields=["username"])

    mock_5.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_6:
        user.delete()

    mock_6.assert_not_called()


def test_webhook__default_setup__for_methods__explicit_deny(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "CREATE": None,
                "UPDATE": None,
                "DELETE": None,
                "M2M_ADD": None,
                "M2M_REMOVE": None,
                "M2M_CLEAR": None,
            },
        },
    }

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_1:
        user.save()

    mock_1.assert_not_called()

    group = Group.objects.create(name="x")
    with patch("signal_webhooks.handlers.default_hook_handler") as mock_2:
        user.groups.add(group)

    mock_2.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_3:
        user.groups.remove(group)

    mock_3.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_4:
        user.groups.clear()

    mock_4.assert_not_called()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_5:
        user.save(update_fields=["username"])

    mock_5.assert_not_called()

    with patch("signal_webhooks.handlers.default_hook_handler") as mock_6:
        user.delete()

    mock_6.assert_not_called()


def test_webhook__custom_setup(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "CREATE": "tests.conftest.mock_hook",
                "UPDATE": "tests.conftest.mock_hook",
                "DELETE": "tests.conftest.mock_hook",
                "M2M_ADD": "tests.conftest.mock_hook",
                "M2M_REMOVE": "tests.conftest.mock_hook",
                "M2M_CLEAR": "tests.conftest.mock_hook",
            },
        },
    }
    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("tests.conftest.mock_side_effect") as mock_1:
        user.save()

    mock_1.assert_called_once()

    group = Group.objects.create(name="x")
    with patch("tests.conftest.mock_side_effect") as mock_2:
        user.groups.add(group)

    mock_2.assert_called_once()

    with patch("tests.conftest.mock_side_effect") as mock_3:
        user.groups.remove(group)

    mock_3.assert_called_once()

    with patch("tests.conftest.mock_side_effect") as mock_4:
        user.groups.clear()

    mock_4.assert_called_once()

    user.username = "xx"

    with patch("tests.conftest.mock_side_effect") as mock_5:
        user.save(update_fields=["username"])

    mock_5.assert_called_once()

    with patch("tests.conftest.mock_side_effect") as mock_6:
        user.delete()

    mock_6.assert_called_once()


def test_webhook__str(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    hook = Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    assert str(hook) == "foo"


def test_webhook__cannot_create_hook_if_settings_missing(settings):
    hook = Webhook(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    msg = r"""{'ref': ["Webhooks not defined for 'django.contrib.auth.models.User'."]}"""

    with pytest.raises(ValidationError, match=re.escape(msg)):
        hook.full_clean(exclude=["last_failure", "last_success"])


def test_webhook__single_webhook__create(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "CREATE": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_1:
        user.save()

    mock_1.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is not None
    assert hook.last_failure is None


def test_webhook__single_webhook__create__different_model(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "CREATE": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE,
        ref="django.contrib.auth.models.Group",
        endpoint="http://www.example.com/",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock:
        user.save()

    mock.assert_not_called()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is None


def test_webhook__single_webhook__update(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "UPDATE": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.UPDATE,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User.objects.create(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    user.username = "xx"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_1:
        user.save(update_fields=["username"])

    mock_1.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is not None
    assert hook.last_failure is None


def test_webhook__single_webhook__update__different_model(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "UPDATE": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.UPDATE,
        ref="django.contrib.auth.models.Group",
        endpoint="http://www.example.com/",
    )

    user = User.objects.create(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    user.username = "xx"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_1:
        user.save(update_fields=["username"])

    mock_1.assert_not_called()


def test_webhook__single_webhook__delete(settings, mock_user):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "DELETE": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.DELETE,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after model delete
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_1, patch(patch_2) as mock_2:
        mock_user.delete()

    mock_1.assert_called_once()
    mock_2.assert_called_once()


def test_webhook__single_webhook__delete__different_model(settings, mock_user):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "DELETE": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.DELETE,
        ref="django.contrib.auth.models.Group",
        endpoint="http://www.example.com/",
    )

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after model delete
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_1, patch(patch_2) as mock_2:
        mock_user.delete()

    mock_1.assert_not_called()
    mock_2.assert_not_called()


def test_webhook__single_webhook__m2m_add(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "M2M_ADD": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User.objects.create(username="x", email="user@user.com", is_staff=True, is_superuser=True)
    group = Group.objects.create(name="x")

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after m2m changed
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_1, patch(patch_2) as mock_2:
        user.groups.add(group)

    mock_1.assert_called_once()
    mock_2.assert_called_once()


def test_webhook__single_webhook__m2m_add__different_model(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "M2M_ADD": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.M2M,
        ref="django.contrib.auth.models.Group",
        endpoint="http://www.example.com/",
    )

    user = User.objects.create(username="x", email="user@user.com", is_staff=True, is_superuser=True)
    group = Group.objects.create(name="x")

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after m2m changed
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_1, patch(patch_2) as mock_2:
        user.groups.add(group)

    mock_1.assert_not_called()
    mock_2.assert_not_called()


def test_webhook__single_webhook__m2m_remove(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "M2M_REMOVE": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User.objects.create(username="x", email="user@user.com", is_staff=True, is_superuser=True)
    group = Group.objects.create(name="x")
    user.groups.add(group)

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after m2m changed
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_1, patch(patch_2) as mock_2:
        user.groups.remove(group)

    mock_1.assert_called_once()
    mock_2.assert_called_once()


def test_webhook__single_webhook__m2m_remove__different_model(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "M2M_REMOVE": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.M2M,
        ref="django.contrib.auth.models.Group",
        endpoint="http://www.example.com/",
    )

    user = User.objects.create(username="x", email="user@user.com", is_staff=True, is_superuser=True)
    group = Group.objects.create(name="x")
    user.groups.add(group)

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after m2m changed
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_1, patch(patch_2) as mock_2:
        user.groups.remove(group)

    mock_1.assert_not_called()
    mock_2.assert_not_called()


def test_webhook__single_webhook__m2m_clear(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "M2M_CLEAR": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User.objects.create(username="x", email="user@user.com", is_staff=True, is_superuser=True)
    group = Group.objects.create(name="x")
    user.groups.add(group)

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after m2m changed
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_1, patch(patch_2) as mock_2:
        user.groups.clear()

    mock_1.assert_called_once()
    mock_2.assert_called_once()


def test_webhook__single_webhook__m2m_clear__different_model(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "M2M_CLEAR": ...,
            },
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.M2M,
        ref="django.contrib.auth.models.Group",
        endpoint="http://www.example.com/",
    )

    user = User.objects.create(username="x", email="user@user.com", is_staff=True, is_superuser=True)
    group = Group.objects.create(name="x")
    user.groups.add(group)

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after m2m changed
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_1, patch(patch_2) as mock_2:
        user.groups.clear()

    mock_1.assert_not_called()
    mock_2.assert_not_called()


def test_webhook__single_webhook__failure(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(400)) as mock:
        user.save()

    mock.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is not None


def test_webhook__single_webhook__authenticated(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA=='",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
        auth_token="Bearer fv98cq49c83479qc37tcqc3847t6ncscitnsntj",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock:
        user.save()

    mock.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is not None
    assert hook.last_failure is None


def test_webhook__single_webhook__webhook_data(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "tests.my_app.models.MyModel": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="tests.my_app.models.MyModel",
        endpoint="http://www.example.com/",
    )

    item = MyModel(name="x")

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_1:
        item.save()

    mock_1.assert_called_once_with(
        "http://www.example.com/",
        json={"fizz": "buzz"},
        headers={"Content-Type": "application/json"},
    )

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is not None
    assert hook.last_failure is None


def test_webhook__single_webhook__webhook_data__cancel_webhook(settings, caplog):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "tests.my_app.models.MyModel": ...,
        },
    }

    response = Response(204)

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="tests.my_app.models.MyModel",
        endpoint="http://www.example.com/",
    )

    item = MyModel(name="x")

    def func():
        raise WebhookCancelled("Just because.")

    method_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    method_2 = "tests.my_app.models.webhook_function"
    # Sqlite cannot handle updating the Webhook after model delete
    method_3 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(method_1, return_value=response) as m1, patch(method_2, side_effect=func) as m2:
        item.save()

    m1.assert_not_called()
    m2.assert_called_once()

    assert len(caplog.messages) == 1
    assert caplog.messages[0] == (
        "Create webhook for 'tests.my_app.models.MyModel' cancelled before it was sent. Reason given: Just because."
    )
    caplog.clear()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is None

    item.name = "xx"
    with patch(method_1, return_value=response) as m3, patch(method_2, side_effect=func) as m4:
        item.save(update_fields=["name"])

    assert len(caplog.messages) == 1
    assert caplog.messages[0] == (
        "Update webhook for 'tests.my_app.models.MyModel' cancelled before it was sent. Reason given: Just because."
    )
    caplog.clear()

    m3.assert_not_called()
    m4.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is None

    with patch(method_1, return_value=response) as m5, patch(method_3) as m6, patch(method_2, side_effect=func) as m7:
        item.delete()

    assert len(caplog.messages) == 1
    assert caplog.messages[0] == (
        "Delete webhook for 'tests.my_app.models.MyModel' cancelled before it was sent. Reason given: Just because."
    )
    caplog.clear()

    m5.assert_not_called()
    m6.assert_not_called()
    m7.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is None


def test_webhook__single_webhook__webhook_data__data_fetching_failed(settings, caplog):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "tests.my_app.models.MyModel": ...,
        },
    }

    response = Response(204)

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="tests.my_app.models.MyModel",
        endpoint="http://www.example.com/",
    )

    item = MyModel(name="x")

    def func():
        raise Exception("foo")

    method_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    method_2 = "tests.my_app.models.webhook_function"
    # Sqlite cannot handle updating the Webhook after model delete
    method_3 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(method_1, return_value=response) as m1, patch(method_2, side_effect=func) as m2:
        item.save()

    m1.assert_not_called()
    m2.assert_called_once()

    assert len(caplog.messages) == 1
    assert caplog.messages[0] == "Create webhook data for 'tests.my_app.models.MyModel' could not be created."
    caplog.clear()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is None

    item.name = "xx"
    with patch(method_1, return_value=response) as m3, patch(method_2, side_effect=func) as m4:
        item.save(update_fields=["name"])

    assert len(caplog.messages) == 1
    assert caplog.messages[0] == "Update webhook data for 'tests.my_app.models.MyModel' could not be created."
    caplog.clear()

    m3.assert_not_called()
    m4.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is None

    with patch(method_1, return_value=response) as m5, patch(method_3) as m6, patch(method_2, side_effect=func) as m7:
        item.delete()

    assert len(caplog.messages) == 1
    assert caplog.messages[0] == "Delete webhook data for 'tests.my_app.models.MyModel' could not be created."
    caplog.clear()

    m5.assert_not_called()
    m6.assert_not_called()
    m7.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is None


@pytest.mark.parametrize(
    ["signal", "methods", "called"],
    [
        (
            SignalChoices.CREATE,
            ["CREATE"],
            [1, 0, 0, 0, 0, 0],
        ),
        (
            SignalChoices.UPDATE,
            ["UPDATE"],
            [0, 0, 0, 0, 1, 0],
        ),
        (
            SignalChoices.DELETE,
            ["DELETE"],
            [0, 0, 0, 0, 0, 1],
        ),
        (
            SignalChoices.M2M,
            ["M2M_ADD"],
            [0, 1, 0, 0, 0, 0],
        ),
        (
            SignalChoices.M2M,
            ["M2M_REMOVE"],
            [0, 0, 1, 0, 0, 0],
        ),
        (
            SignalChoices.M2M,
            ["M2M_CLEAR"],
            [0, 0, 0, 1, 0, 0],
        ),
        (
            SignalChoices.CREATE_OR_UPDATE,
            ["CREATE", "UPDATE"],
            [1, 0, 0, 0, 1, 0],
        ),
        (
            SignalChoices.CREATE_OR_DELETE,
            ["CREATE", "DELETE"],
            [1, 0, 0, 0, 0, 1],
        ),
        (
            SignalChoices.CREATE_OR_M2M,
            ["CREATE", "M2M_ADD"],
            [1, 1, 0, 0, 0, 0],
        ),
        (
            SignalChoices.CREATE_OR_M2M,
            ["CREATE", "M2M_REMOVE"],
            [1, 0, 1, 0, 0, 0],
        ),
        (
            SignalChoices.CREATE_OR_M2M,
            ["CREATE", "M2M_CLEAR"],
            [1, 0, 0, 1, 0, 0],
        ),
        (
            SignalChoices.UPDATE_OR_DELETE,
            ["UPDATE", "DELETE"],
            [0, 0, 0, 0, 1, 1],
        ),
        (
            SignalChoices.UPDATE_OR_M2M,
            ["UPDATE", "M2M_ADD"],
            [0, 1, 0, 0, 1, 0],
        ),
        (
            SignalChoices.UPDATE_OR_M2M,
            ["UPDATE", "M2M_REMOVE"],
            [0, 0, 1, 0, 1, 0],
        ),
        (
            SignalChoices.UPDATE_OR_M2M,
            ["UPDATE", "M2M_CLEAR"],
            [0, 0, 0, 1, 1, 0],
        ),
        (
            SignalChoices.DELETE_OR_M2M,
            ["DELETE", "M2M_ADD"],
            [0, 1, 0, 0, 0, 1],
        ),
        (
            SignalChoices.DELETE_OR_M2M,
            ["DELETE", "M2M_REMOVE"],
            [0, 0, 1, 0, 0, 1],
        ),
        (
            SignalChoices.DELETE_OR_M2M,
            ["DELETE", "M2M_CLEAR"],
            [0, 0, 0, 1, 0, 1],
        ),
        (
            SignalChoices.CREATE_UPDATE_OR_DELETE,
            ["CREATE", "UPDATE", "DELETE"],
            [1, 0, 0, 0, 1, 1],
        ),
        (
            SignalChoices.CREATE_UPDATE_OR_M2M,
            ["CREATE", "UPDATE", "M2M_ADD"],
            [1, 1, 0, 0, 1, 0],
        ),
        (
            SignalChoices.CREATE_UPDATE_OR_M2M,
            ["CREATE", "UPDATE", "M2M_REMOVE"],
            [1, 0, 1, 0, 1, 0],
        ),
        (
            SignalChoices.CREATE_UPDATE_OR_M2M,
            ["CREATE", "UPDATE", "M2M_CLEAR"],
            [1, 0, 0, 1, 1, 0],
        ),
        (
            SignalChoices.CREATE_DELETE_OR_M2M,
            ["CREATE", "DELETE", "M2M_ADD"],
            [1, 1, 0, 0, 0, 1],
        ),
        (
            SignalChoices.CREATE_DELETE_OR_M2M,
            ["CREATE", "DELETE", "M2M_REMOVE"],
            [1, 0, 1, 0, 0, 1],
        ),
        (
            SignalChoices.CREATE_DELETE_OR_M2M,
            ["CREATE", "DELETE", "M2M_CLEAR"],
            [1, 0, 0, 1, 0, 1],
        ),
        (
            SignalChoices.UPDATE_DELETE_OR_M2M,
            ["UPDATE", "DELETE", "M2M_ADD"],
            [0, 1, 0, 0, 1, 1],
        ),
        (
            SignalChoices.UPDATE_DELETE_OR_M2M,
            ["UPDATE", "DELETE", "M2M_REMOVE"],
            [0, 0, 1, 0, 1, 1],
        ),
        (
            SignalChoices.UPDATE_DELETE_OR_M2M,
            ["UPDATE", "DELETE", "M2M_CLEAR"],
            [0, 0, 0, 1, 1, 1],
        ),
        (
            SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
            ["CREATE", "UPDATE", "DELETE", "M2M_ADD", "M2M_REMOVE", "M2M_CLEAR"],
            [1, 1, 1, 1, 1, 1],
        ),
    ],
)
def test_webhook__single_webhook__correct_signal(settings, signal, methods, called):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {m: ... for m in methods},
        },
    }

    called = iter(called)

    Webhook.objects.create(
        name="foo",
        signal=signal,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_1, patch(patch_2):
        user.save()

    assert mock_1.call_count == next(called)

    group = Group.objects.create(name="x")
    with patch(patch_1, return_value=Response(204)) as mock_2, patch(patch_2):
        user.groups.add(group)

    assert mock_2.call_count == next(called)

    with patch(patch_1, return_value=Response(204)) as mock_3, patch(patch_2):
        user.groups.remove(group)

    assert mock_3.call_count == next(called)

    with patch(patch_1, return_value=Response(204)) as mock_4, patch(patch_2):
        user.groups.clear()

    assert mock_4.call_count == next(called)

    user.username = "xx"

    with patch(patch_1, return_value=Response(204)) as mock_5, patch(patch_2):
        user.save(update_fields=["username"])

    assert mock_5.call_count == next(called)

    with patch(patch_1, return_value=Response(204)) as mock_6, patch(patch_2):
        user.delete()

    assert mock_6.call_count == next(called)


def test_webhook__single_webhook__disable_hooks_dont_fire(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
        enabled=False,
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_1:
        user.save()

    mock_1.assert_not_called()

    user.username = "xx"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_not_called()

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after model delete
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_3, patch(patch_2) as mock_4:
        user.delete()

    mock_3.assert_not_called()
    mock_4.assert_not_called()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is None


def test_webhook__single_webhook__keep_response(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
        keep_last_response=True,
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    resp = Response(204)
    resp._content = b"bar"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=resp) as mock:
        user.save()

    mock.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is not None
    assert hook.last_failure is None
    assert hook.last_response == "bar"


def test_webhook__single_webhook__dont_keep_response(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
        keep_last_response=False,
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    resp = Response(204)
    resp._content = b"bar"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=resp) as mock:
        user.save()

    mock.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is not None
    assert hook.last_failure is None
    assert hook.last_response == ""


def test_webhook__single_webhook__keep_response__failure(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
        keep_last_response=True,
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    resp = Response(400)
    resp._content = b"bar"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=resp) as mock:
        user.save()

    mock.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is not None
    assert hook.last_response == "bar"


def test_webhook__single_webhook__sending_timeout(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "TIMEOUT": 1,
        "HOOKS": {
            "tests.my_app.models.MyModel": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="tests.my_app.models.MyModel",
        endpoint="http://www.example.com/",
    )

    user = MyModel(name="x")

    # Patch the 'anyio.abc._streams.ByteStream' reveiver
    # to wait until 'httpx._client.AsyncClient' is timed out.
    async def mock_reveive(*args, **kwargs) -> bytes:
        await asyncio.sleep(3)
        return b""

    receiver = "anyio._backends._asyncio.SocketStream.receive"  # http
    # receiver = "anyio.streams.tls.TLSStream.receive"  # https

    with patch(receiver, side_effect=mock_reveive, new_callable=AsyncMock) as mock_1:
        user.save()

    mock_1.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is None
    assert hook.last_failure is not None


def test_webhook__single_webhook__thread_task_handler(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.thread_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock:
        user.save()

        # wait for the thread to finnish
        sleep(1)

    mock.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is not None
    assert hook.last_failure is None


def test_webhook__multiple_webhooks(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    Webhook.objects.create(
        name="bar",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example1.com/",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock:
        user.save()

    mock.assert_called()
    assert mock.call_count == 2

    hook_1 = Webhook.objects.get(name="foo")
    hook_2 = Webhook.objects.get(name="bar")

    assert hook_1.last_success is not None
    assert hook_1.last_failure is None

    assert hook_2.last_success is not None
    assert hook_2.last_failure is None


def test_webhook__multiple_webhooks__failure(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    Webhook.objects.create(
        name="bar",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example1.com/",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(400)) as mock:
        user.save()

    mock.assert_called()
    assert mock.call_count == 2

    hook_1 = Webhook.objects.get(name="foo")
    hook_2 = Webhook.objects.get(name="bar")

    assert hook_1.last_success is None
    assert hook_1.last_failure is not None

    assert hook_2.last_success is None
    assert hook_2.last_failure is not None


def test_webhook__multiple_webhooks__sending_timeout(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "TIMEOUT": 1,
        "HOOKS": {
            "tests.my_app.models.MyModel": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="tests.my_app.models.MyModel",
        endpoint="http://www.example.com/",
    )

    Webhook.objects.create(
        name="bar",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="tests.my_app.models.MyModel",
        endpoint="http://www.example1.com/",
    )

    user = MyModel(name="x")

    # Patch the 'anyio.abc._streams.ByteStream' reveiver
    # to wait until 'httpx._client.AsyncClient' is timed out.
    async def mock_reveive(*args, **kwargs) -> bytes:
        await asyncio.sleep(3)
        return b""

    receiver = "anyio._backends._asyncio.SocketStream.receive"  # http
    # receiver = "anyio.streams.tls.TLSStream.receive"  # https

    with patch(receiver, side_effect=mock_reveive, new_callable=AsyncMock) as mock:
        user.save()

    mock.assert_called()
    assert mock.call_count == 2

    hook_1 = Webhook.objects.get(name="foo")
    hook_2 = Webhook.objects.get(name="bar")

    assert hook_1.last_success is None
    assert hook_1.last_failure is not None

    assert hook_2.last_success is None
    assert hook_2.last_failure is not None


def test_webhook__swapped_webhook_model(settings):
    get_webhook_model.cache_clear()  # Clear lru_cache

    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    settings.SIGNAL_WEBHOOKS_CUSTOM_MODEL = "tests.my_app.models.MyWebhook"

    MyWebhook.objects.create(
        code="123",
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_1:
        user.save()

    mock_1.assert_called_once()

    hook = MyWebhook.objects.get(name="foo")

    assert hook.last_success is not None
    assert hook.last_failure is None


def test_webhook__swapped_webhook_model__import_failed(settings):
    get_webhook_model.cache_clear()  # Clear lru_cache

    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    settings.SIGNAL_WEBHOOKS_CUSTOM_MODEL = "tests.my_app.models.MyWebhooks"

    MyWebhook.objects.create(
        code="123",
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    msg = "'tests.my_app.models.MyWebhooks' is not a model that can be imported."

    with pytest.raises(ImproperlyConfigured, match=re.escape(msg)):
        user.save()


def test_webhook__swapped_webhook_model__not_a_webhook(settings):
    get_webhook_model.cache_clear()  # Clear lru_cache

    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    settings.SIGNAL_WEBHOOKS_CUSTOM_MODEL = "tests.my_app.models.MyModel"

    MyWebhook.objects.create(
        code="123",
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    msg = "'tests.my_app.models.MyModel' is not a subclass of a 'signal_webhooks.models.WebhookBase'."

    with pytest.raises(ImproperlyConfigured, match=re.escape(msg)):
        user.save()

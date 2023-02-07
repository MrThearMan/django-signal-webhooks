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
from signal_webhooks.utils import get_webhookhook_model
from tests.my_app.models import MyModel, MyWebhook


@pytest.mark.django_db
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

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_1:
        user.save()

    mock_1.assert_called_once()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_called_once()

    with patch("signal_webhooks.handlers.default_post_delete_handler") as mock_3:
        user.delete()

    mock_3.assert_called_once()

    group = Group(name="x")

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_4:
        group.save()

    mock_4.assert_not_called()

    group.name = "xx"

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_5:
        group.save(update_fields=["name"])

    mock_5.assert_not_called()

    with patch("signal_webhooks.handlers.default_post_delete_handler") as mock_6:
        group.delete()

    mock_6.assert_not_called()


@pytest.mark.django_db
def test_webhook__default_setup__expicit_deny(settings):
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

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_1:
        user.save()

    mock_1.assert_not_called()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_not_called()

    with patch("signal_webhooks.handlers.default_post_delete_handler") as mock_3:
        user.delete()

    mock_3.assert_not_called()


@pytest.mark.django_db
def test_webhook__default_setup__for_methods(settings):

    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "CREATE": ...,
                "UPDATE": ...,
                "DELETE": ...,
            },
        },
    }

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_1:
        user.save()

    mock_1.assert_called_once()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_called_once()

    with patch("signal_webhooks.handlers.default_post_delete_handler") as mock_3:
        user.delete()

    mock_3.assert_called_once()


@pytest.mark.django_db
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

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_1:
        user.save()

    mock_1.assert_not_called()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_not_called()

    with patch("signal_webhooks.handlers.default_post_delete_handler") as mock_3:
        user.delete()

    mock_3.assert_not_called()


@pytest.mark.django_db
def test_webhook__default_setup__for_methods__set_none(settings):

    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "CREATE": None,
                "UPDATE": None,
                "DELETE": None,
            },
        },
    }

    user = User(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_1:
        user.save()

    mock_1.assert_not_called()

    user.username = "xx"

    with patch("signal_webhooks.handlers.default_post_save_handler") as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_not_called()

    with patch("signal_webhooks.handlers.default_post_delete_handler") as mock_3:
        user.delete()

    mock_3.assert_not_called()


@pytest.mark.django_db
def test_webhook__custom_setup(settings):

    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": {
                "CREATE": "tests.conftest.mock_hook",
                "UPDATE": "tests.conftest.mock_hook",
                "DELETE": "tests.conftest.mock_hook",
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

    user.username = "xx"

    with patch("tests.conftest.mock_side_effect") as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_called_once()

    with patch("tests.conftest.mock_side_effect") as mock_3:
        user.delete()

    mock_3.assert_called_once()


@pytest.mark.django_db
def test_webhook__str(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    hook = Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    assert str(hook) == "foo"


@pytest.mark.django_db
def test_webhook__cannot_create_hook_if_settings_missing(settings):
    hook = Webhook(
        name="foo",
        signal=SignalChoices.ALL,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    msg = r"""{'ref': ["Webhooks not defined for 'django.contrib.auth.models.User'."]}"""

    with pytest.raises(ValidationError, match=re.escape(msg)):
        hook.full_clean(exclude=["last_failure", "last_success"])


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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

    user.username = "xx"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_called_once()

    hook = Webhook.objects.get(name="foo")

    assert hook.last_success is not None
    assert hook.last_failure is None


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__failure(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
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
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__different_model(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__delete(settings, mock_user):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__delete__different_model(settings, mock_user):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__webhook_data(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "tests.my_app.models.MyModel": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
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
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
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
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__correct_signal__create_only(settings):
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

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_1:
        user.save()

    mock_1.assert_called_once()

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


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__correct_signal__update_only(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.UPDATE,
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

    mock_1.assert_not_called()

    user.username = "xx"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_called_once()

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after model delete
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_3, patch(patch_2) as mock_4:
        user.delete()

    mock_3.assert_not_called()
    mock_4.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__correct_signal__delete_only(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.DELETE,
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

    mock_3.assert_called_once()
    mock_4.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__correct_signal__create_or_update(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_OR_UPDATE,
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

    user.username = "xx"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_called_once()

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after model delete
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_3, patch(patch_2) as mock_4:
        user.delete()

    mock_3.assert_not_called()
    mock_4.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__correct_signal__create_or_delete(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_OR_DELETE,
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

    user.username = "xx"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_not_called()

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after model delete
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_3, patch(patch_2) as mock_4:
        user.delete()

    mock_3.assert_called_once()
    mock_4.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__correct_signal__update_or_delete(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.UPDATE_OR_DELETE,
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

    mock_1.assert_not_called()

    user.username = "xx"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_called_once()

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after model delete
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_3, patch(patch_2) as mock_4:
        user.delete()

    mock_3.assert_called_once()
    mock_4.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__correct_signal__all(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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

    user.username = "xx"

    with patch("signal_webhooks.handlers.httpx.AsyncClient.post", return_value=Response(204)) as mock_2:
        user.save(update_fields=["username"])

    mock_2.assert_called_once()

    patch_1 = "signal_webhooks.handlers.httpx.AsyncClient.post"
    # Sqlite cannot handle updating the Webhook after model delete
    patch_2 = "signal_webhooks.models.Webhook.objects.bulk_update"

    with patch(patch_1, return_value=Response(204)) as mock_3, patch(patch_2) as mock_4:
        user.delete()

    mock_3.assert_called_once()
    mock_4.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__disable_hooks_dont_fire(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__keep_response(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__dont_keep_response(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__keep_response__failure(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
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
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__single_webhook__thread_task_handler(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.thread_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__multiple_webhooks(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    Webhook.objects.create(
        name="bar",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__multiple_webhooks__failure(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    Webhook.objects.create(
        name="foo",
        signal=SignalChoices.ALL,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
    )

    Webhook.objects.create(
        name="bar",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
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
        signal=SignalChoices.ALL,
        ref="tests.my_app.models.MyModel",
        endpoint="http://www.example.com/",
    )

    Webhook.objects.create(
        name="bar",
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__swapped_webhook_model(settings):
    get_webhookhook_model.cache_clear()  # Clear lru_cache

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
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__swapped_webhook_model__import_failed(settings):
    get_webhookhook_model.cache_clear()  # Clear lru_cache

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
        signal=SignalChoices.ALL,
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


@pytest.mark.django_db(transaction=True)
def test_webhook__swapped_webhook_model__not_a_webhook(settings):
    get_webhookhook_model.cache_clear()  # Clear lru_cache

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
        signal=SignalChoices.ALL,
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

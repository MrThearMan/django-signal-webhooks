import re
from datetime import datetime

import pytest
from django.core.exceptions import ValidationError

from signal_webhooks.admin import WebhookModelForm
from signal_webhooks.models import Webhook
from signal_webhooks.typing import SignalChoices

pytestmark = [
    pytest.mark.django_db,
]


def test_add_webhook_in_admin_panel(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    token = "Bearer fv98cq49c83479qc37tcqc3847t6ncscitnsntj"

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        "auth_token": token,
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.is_valid()

    form.save()

    assert form.instance.id == 1
    assert form.instance.name == "foo"
    assert form.instance.signal == SignalChoices.CREATE_UPDATE_DELETE_OR_M2M
    assert form.instance.ref == "django.contrib.auth.models.User"
    assert form.instance.auth_token == token


def test_add_webhook_in_admin_panel__auth_token_hidden(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": True,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    token = "Bearer fv98cq49c83479qc37tcqc3847t6ncscitnsntj"

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        "auth_token": token,
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # These are set if auth_token should be hidden
    assert hasattr(form, "_auth_token")
    assert form._auth_token is None

    assert form.instance.id is None  # Nothing saved yet
    assert form.is_valid()

    form.save()

    assert form.instance.id == 1
    assert form.instance.name == "foo"
    assert form.instance.signal == SignalChoices.CREATE_UPDATE_DELETE_OR_M2M
    assert form.instance.ref == "django.contrib.auth.models.User"

    # Confirm that token is saved corretly
    assert form.instance.auth_token == token


def test_add_webhook_in_admin_panel__check_headers(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        "headers": {"foo": "bar"},
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.is_valid()

    form.save()

    assert form.instance.id == 1
    assert form.instance.name == "foo"
    assert form.instance.signal == SignalChoices.CREATE_UPDATE_DELETE_OR_M2M
    assert form.instance.ref == "django.contrib.auth.models.User"
    assert form.instance.headers == {"foo": "bar"}


def test_add_webhook_in_admin_panel__check_headers__not_a_dict(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        "headers": [{"foo": "bar"}],
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"headers": ["Headers should always be a dict."]}


def test_add_webhook_in_admin_panel__check_model_ref__hooks_not_defined(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.Group",
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"ref": ["Webhooks not defined for 'django.contrib.auth.models.Group'."]}


def test_add_webhook_in_admin_panel__check_model_ref__not_a_model(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.AnonymousUser",
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"ref": ["'django.contrib.auth.models.AnonymousUser' is not a django model."]}


def test_add_webhook_in_admin_panel__name_missing(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"name": ["This field is required."]}


def test_add_webhook_in_admin_panel__signal_missing(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"signal": ["This field is required."]}


def test_add_webhook_in_admin_panel__ref_missing(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"ref": ["This field is required."]}


def test_add_webhook_in_admin_panel__endpoint_missing(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"endpoint": ["This field is required."]}


def test_add_webhook_in_admin_panel__prevent_duplicate_hooks(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.is_valid()

    form.save()

    assert len(Webhook.objects.all()) == 1

    data = {
        "name": "bar",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"__all__": ["Webhook with this Referenced model and Endpoint already exists."]}


def test_add_webhook_in_admin_panel__unique_name(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example1.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.is_valid()

    form.save()

    assert len(Webhook.objects.all()) == 1

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example2.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"name": ["Webhook with this Name already exists."]}


def test_add_webhook_in_admin_panel__cipher_key_missing__no_token(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.is_valid()

    form.save()

    assert form.instance.id == 1
    assert form.instance.name == "foo"
    assert form.instance.signal == SignalChoices.CREATE_UPDATE_DELETE_OR_M2M
    assert form.instance.ref == "django.contrib.auth.models.User"
    assert form.instance.auth_token == ""


def test_add_webhook_in_admin_panel__cipher_key_missing__token_given(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    token = "Bearer fv98cq49c83479qc37tcqc3847t6ncscitnsntj"

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        "auth_token": token,
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"auth_token": ["Cipher key not set."]}


def test_add_webhook_in_admin_panel__cipher_key_invalid__token_given(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "foo",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    token = "Bearer fv98cq49c83479qc37tcqc3847t6ncscitnsntj"

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        "auth_token": token,
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"auth_token": ["Invalid cipher key."]}


def test_add_webhook_in_admin_panel__cipher_key_old(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    token = "Bearer fv98cq49c83479qc37tcqc3847t6ncscitnsntj"

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        "auth_token": token,
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.is_valid()

    form.save()

    assert form.instance.id == 1
    assert form.instance.name == "foo"
    assert form.instance.signal == SignalChoices.CREATE_UPDATE_DELETE_OR_M2M
    assert form.instance.ref == "django.contrib.auth.models.User"
    assert form.instance.auth_token == token

    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "BmMj3p7In2m22pPwhGk+FA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    msg = "Wrong cipher key."

    with pytest.raises(ValidationError, match=re.escape(msg)):
        Webhook.objects.get(name="foo")


def test_add_webhook_in_admin_panel__check_model_ref__not_exists(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.Users",
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {
        "ref": [
            "Could not import 'django.contrib.auth.models.Users'. "
            "Module 'django.contrib.auth.models' does not define 'Users'."
        ]
    }


def test_add_webhook_in_admin_panel__check_model_ref__not_proper_import(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": False,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "foo",
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(data=data)

    # For when HIDE_TOKEN is True
    assert not hasattr(form, "_auth_token")

    assert form.instance.id is None  # Nothing saved yet
    assert form.errors == {"ref": ["Could not import 'foo'. 'foo' doesn't look like a module path."]}


def test_update_webhook_in_admin_panel__auth_token_hidden(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HIDE_TOKEN": True,
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    token = "Bearer fv98cq49c83479qc37tcqc3847t6ncscitnsntj"

    hook = Webhook.objects.create(
        name="foo",
        signal=SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        ref="django.contrib.auth.models.User",
        endpoint="http://www.example.com/",
        auth_token=token,
    )

    data = {
        "name": "foo",
        "signal": SignalChoices.CREATE_UPDATE_DELETE_OR_M2M,
        "ref": "django.contrib.auth.models.User",
        "endpoint": "http://www.example.com/",
        # Must be given due to 'auto_now' and 'auto_now_add'
        "last_success": datetime(2022, 1, 1),
        "last_failure": datetime(2022, 1, 1),
    }

    form = WebhookModelForm(instance=hook, data=data)

    # Token should be hidden
    assert hasattr(form, "_auth_token")
    assert form._auth_token == token
    assert form.instance.auth_token == ""
    assert "Current token: ********nsntj" in form.fields["auth_token"].help_text

    assert form.is_valid()

    form.save()

    assert form.instance.id == 1
    assert form.instance.name == "foo"
    assert form.instance.signal == SignalChoices.CREATE_UPDATE_DELETE_OR_M2M
    assert form.instance.ref == "django.contrib.auth.models.User"

    # Token is still retained even if (new) token is not given in data
    assert form.instance.auth_token == token

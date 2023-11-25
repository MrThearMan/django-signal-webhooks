import random
import re
import string

import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from signal_webhooks.typing import MAX_COL_SIZE
from signal_webhooks.utils import (
    decode_cipher_key,
    default_serializer,
    is_dict,
    model_from_reference,
    random_cipher_key,
    truncate,
)
from tests.my_app.models import MyModel


def test_model_from_reference(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    model = model_from_reference("django.contrib.auth.models.User")

    assert model == User


def test_model_from_reference__not_a_dot_import(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    msg = "Could not import 'foo'. 'foo' doesn't look like a module path."

    with pytest.raises(ValidationError, match=re.escape(msg)):
        model_from_reference("foo")


def test_model_from_reference__does_no_define_given_value(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    msg = (
        "Could not import 'django.contrib.auth.models.Users'. "
        "Module 'django.contrib.auth.models' does not define 'Users'."
    )

    with pytest.raises(ValidationError, match=re.escape(msg)):
        model_from_reference("django.contrib.auth.models.Users")


def test_model_from_reference__not_a_model(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.User": ...,
        },
    }

    msg = "'django.contrib.auth.models.AnonymousUser' is not a django model."

    with pytest.raises(ValidationError, match=re.escape(msg)):
        model_from_reference("django.contrib.auth.models.AnonymousUser")


def test_model_from_reference__webhooks_not_defined(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "HOOKS": {
            "django.contrib.auth.models.Group": ...,
        },
    }

    msg = "Webhooks not defined for 'django.contrib.auth.models.User'."

    with pytest.raises(ValidationError, match=re.escape(msg)):
        model_from_reference("django.contrib.auth.models.User")


def test_random_cipher_key():
    assert len(random_cipher_key()) == 24
    assert len(random_cipher_key(16)) == 24
    assert len(random_cipher_key(24)) == 32
    assert len(random_cipher_key(32)) == 44


def test_decode_cipher_key(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "CIPHER_KEY": "l0vavU2k5az8A+OD2jd3oA==",
    }

    assert len(decode_cipher_key()) == 16


def test_decode_cipher_key__invalid_key(settings):
    settings.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
        "CIPHER_KEY": "foo",
    }

    msg = "Invalid cipher key."

    with pytest.raises(ValidationError, match=re.escape(msg)):
        decode_cipher_key()


def test_decode_cipher_key__not_set(settings):
    msg = "Cipher key not set."

    with pytest.raises(ValidationError, match=re.escape(msg)):
        decode_cipher_key()


def test_is_dict():
    is_dict({"foo": "bar"})


def test_is_dict__fail():
    msg = "Headers should always be a dict."

    with pytest.raises(ValidationError, match=re.escape(msg)):
        is_dict([{"foo": "bar"}])


def test_truncate():
    len_max = "".join(random.choice(string.ascii_letters) for _ in range(MAX_COL_SIZE))
    len_over = "".join(random.choice(string.ascii_letters) for _ in range(MAX_COL_SIZE + 1))

    assert len(truncate(len_max)) == MAX_COL_SIZE
    assert len(truncate(len_over)) == MAX_COL_SIZE


@freeze_time("2022-01-01T00:00:00")
@pytest.mark.django_db()
def test_default_serializer__user():
    user = User.objects.create(
        username="x",
        email="user@user.com",
        is_staff=True,
        is_superuser=True,
    )

    data = default_serializer(user)

    assert data == {
        "fields": {
            "date_joined": "2022-01-01 00:00:00+00:00",
            "email": "user@user.com",
            "first_name": "",
            "groups": [],
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
            "last_login": None,
            "last_name": "",
            "password": "",
            "user_permissions": [],
            "username": "x",
        },
        "model": "auth.user",
        "pk": 1,
    }


@pytest.mark.django_db()
def test_default_serializer__group():
    group = Group.objects.create(name="x")

    data = default_serializer(group)

    assert data == {
        "fields": {
            "name": "x",
            "permissions": [],
        },
        "model": "auth.group",
        "pk": 1,
    }


@pytest.mark.django_db()
def test_default_serializer__mymodel():
    mymodel = MyModel.objects.create(name="x")

    data = default_serializer(mymodel)

    assert data == {"fizz": "buzz"}

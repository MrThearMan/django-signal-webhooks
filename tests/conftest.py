import pytest
from django.contrib.auth.models import User
from settings_holder import SettingsWrapper


@pytest.fixture(scope="session", autouse=True)
def setup_django_settings():
    wrapper = SettingsWrapper()
    wrapper.DEBUG = False
    wrapper.SIGNAL_WEBHOOKS = {
        "TASK_HANDLER": "signal_webhooks.handlers.sync_task_handler",
    }

    yield
    wrapper.finalize()


@pytest.fixture()
def settings():
    wrapper = SettingsWrapper()
    try:
        yield wrapper
    finally:
        wrapper.finalize()


@pytest.fixture()
def mock_user(django_db_blocker) -> User:
    with django_db_blocker.unblock():
        return User.objects.create(
            username="x",
            email="user@user.com",
            is_staff=True,
            is_superuser=True,
        )


def mock_hook(**kwargs):
    mock_side_effect()


def mock_side_effect():
    pass

import asyncio
import logging
from base64 import b64decode, b64encode
from functools import lru_cache
from importlib import import_module
from os import urandom
from sys import modules

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models import Model
from django.db.models.base import ModelBase

from .serializers import webhook_serializer
from .settings import webhook_settings
from .typing import TYPE_CHECKING, Any, ClientMethodKwargs, Generator, JSONData, Literal, Set, Type


if TYPE_CHECKING:
    from .models import Webhook, WebhookBase


__all__ = [
    "decode_cipher_key",
    "default_client_kwargs",
    "default_serializer",
    "get_webhookhook_model",
    "is_dict",
    "model_from_reference",
    "random_cipher_key",
    "reference_for_model",
    "tasks_as_completed",
    "truncate",
]


logger = logging.getLogger(__name__)


def is_dict(value: str) -> None:
    if not isinstance(value, dict):
        raise ValidationError("Headers should always be a dict.")


def truncate(string: str, limit: int = 10_000) -> str:
    if len(string) > limit:
        string = string[: limit - 3] + "..."
    return string


def random_cipher_key(length: Literal[16, 24, 32] = 16) -> str:
    return b64encode(urandom(length)).decode()


# 'value' as parameter so that can be used as a field validator
def decode_cipher_key(value: str = "") -> bytes:  # pylint: disable=unused-argument
    try:
        return b64decode(webhook_settings.CIPHER_KEY)
    except TypeError as error:
        raise ValidationError("Cipher key not set.") from error
    except Exception as error:  # pylint: disable=broad-except
        raise ValidationError("Invalid cipher key.") from error


def default_serializer(instance: Model) -> JSONData:
    if hasattr(instance, "webhook_data") and callable(instance.webhook_data):
        return instance.webhook_data()

    return webhook_serializer.serialize([instance])


def default_client_kwargs(hook: "Webhook") -> ClientMethodKwargs:  # pylint: disable=unused-argument
    return ClientMethodKwargs()


@lru_cache(maxsize=None)
def get_webhookhook_model() -> Type["WebhookBase"]:
    ref = getattr(settings, "SIGNAL_WEBHOOKS_CUSTOM_MODEL", "signal_webhooks.models.Webhook")

    if ref == "signal_webhooks.models.Webhook":
        from .models import Webhook  # pylint: disable=import-outside-toplevel

        return Webhook

    try:
        model = model_from_reference(ref, check_hooks=False)
    except ValidationError as error:
        raise ImproperlyConfigured(f"{ref!r} is not a model that can be imported.") from error

    from .models import WebhookBase  # pylint: disable=import-outside-toplevel

    if not issubclass(model, WebhookBase):
        base_ref = reference_for_model(WebhookBase)
        raise ImproperlyConfigured(f"{ref!r} is not a subclass of a {base_ref!r}.")

    return model


def model_from_reference(ref: str, check_hooks: bool = True) -> ModelBase:
    msg = f"Could not import {ref!r}"
    try:
        module_path, class_name = ref.rsplit(".", 1)
    except ValueError as error:
        raise ValidationError(f"{msg}. {ref!r} doesn't look like a module path.") from error

    if module_path not in modules or (
        # Module is not fully initialized.
        getattr(modules[module_path], "__spec__", None) is not None
        and getattr(modules[module_path].__spec__, "_initializing", False) is True
    ):  # pragma: no cover
        try:
            import_module(module_path)
        except ImportError as error:
            raise ValidationError(f"{msg}. {error.__class__.__name__!r}: {error}.") from error

    try:
        model_type = getattr(modules[module_path], class_name)
    except AttributeError as error:
        raise ValidationError(f"{msg}. Module {module_path!r} does not define {class_name!r}.") from error

    if not isinstance(model_type, ModelBase):
        raise ValidationError(f"{ref!r} is not a django model.")

    if check_hooks and ref not in webhook_settings.HOOKS:
        raise ValidationError(f"Webhooks not defined for {ref!r}.")

    return model_type


def reference_for_model(model: ModelBase) -> str:
    return f"{model.__module__}.{model.__name__}"


async def tasks_as_completed(tasks: Set[asyncio.Task]) -> Generator[asyncio.Task, Any, None]:
    done = asyncio.Queue()

    def _on_completion(task_: asyncio.Task) -> None:
        tasks.remove(task_)
        done.put_nowait(task_)

    async def _wait_for_one() -> asyncio.Task:
        return await done.get()

    for task in tasks:
        task.add_done_callback(_on_completion)

    for _ in range(len(tasks)):
        yield await _wait_for_one()

import asyncio
import logging
from datetime import datetime, timezone
from threading import Thread
from typing import Any

import httpx
from asgiref.sync import sync_to_async
from django.db.models import QuerySet, signals
from django.db.models.base import ModelBase
from django.dispatch import receiver

from .settings import webhook_settings
from .typing import (
    TYPE_CHECKING,
    Callable,
    ClientMethodKwargs,
    Dict,
    HooksData,
    JSONData,
    Optional,
    PostDeleteData,
    PostSaveData,
    Set,
    SignalChoices,
)
from .utils import get_webhookhook_model, reference_for_model, tasks_as_completed, truncate


if TYPE_CHECKING:
    from .models import Webhook


__all__ = [
    "default_error_handler",
    "default_post_delete_handler",
    "default_post_save_handler",
    "sync_task_handler",
    "thread_task_handler",
    "webhook_delete_handler",
    "webhook_update_create_handler",
]


logger = logging.getLogger(__name__)


@receiver(signals.post_save, dispatch_uid=webhook_settings.DISPATCH_UID_POST_SAVE)
def webhook_update_create_handler(sender: ModelBase, **kwargs) -> None:  # pylint: disable=unused-argument
    kwargs: PostSaveData
    ref = reference_for_model(type(kwargs["instance"]))

    hooks: Optional[HooksData] = webhook_settings.HOOKS.get(ref)
    if hooks is None:
        return
    if hooks is ...:
        webhook_settings.TASK_HANDLER(
            default_post_save_handler,
            ref=ref,
            data=webhook_settings.SERIALIZER(kwargs["instance"]),
            created=kwargs["created"],
        )
        return

    hook = hooks.get("CREATE") if kwargs["created"] else hooks.get("UPDATE")

    if hook is None:
        return
    if hook is ...:
        webhook_settings.TASK_HANDLER(
            default_post_save_handler,
            ref=ref,
            data=webhook_settings.SERIALIZER(kwargs["instance"]),
            created=kwargs["created"],
        )
        return

    webhook_settings.TASK_HANDLER(
        hook,
        ref=ref,
        data=webhook_settings.SERIALIZER(kwargs["instance"]),
        created=kwargs["created"],
    )


@receiver(signals.post_delete, dispatch_uid=webhook_settings.DISPATCH_UID_POST_DELETE)
def webhook_delete_handler(sender: ModelBase, **kwargs) -> None:  # pylint: disable=unused-argument
    kwargs: PostDeleteData
    ref = reference_for_model(type(kwargs["instance"]))

    hooks: Optional[HooksData] = webhook_settings.HOOKS.get(ref)
    if hooks is None:
        return
    if hooks is ...:
        webhook_settings.TASK_HANDLER(
            default_post_delete_handler,
            ref=ref,
            data=webhook_settings.SERIALIZER(kwargs["instance"]),
        )
        return

    hook = hooks.get("DELETE")

    if hook is None:
        return
    if hook is ...:
        webhook_settings.TASK_HANDLER(
            default_post_delete_handler,
            ref=ref,
            data=webhook_settings.SERIALIZER(kwargs["instance"]),
        )
        return

    webhook_settings.TASK_HANDLER(
        hook,
        ref=ref,
        data=webhook_settings.SERIALIZER(kwargs["instance"]),
    )


def default_error_handler(hook: "Webhook", error: Optional[Exception]) -> None:  # pylint: disable=unused-argument
    """Default handler for errors from webhooks.

    :param hook: Hook that failed
    :param error: Exception if one was caused due to, e.g., timeout.
    """


def thread_task_handler(hook: Callable[..., None], **kwargs: Any) -> None:
    thread = Thread(target=hook, kwargs=kwargs)
    thread.start()


def sync_task_handler(hook: Callable[..., None], **kwargs: Any) -> None:
    hook(**kwargs)


def default_post_save_handler(ref: str, data: JSONData, created: bool) -> None:
    webhook_model = get_webhookhook_model()

    signal_types = SignalChoices.create_choises() if created else SignalChoices.update_choises()
    hooks = webhook_model.objects.get_for_ref(ref, signals=signal_types)

    if not hooks.exists():
        return

    method_data: Dict[int, ClientMethodKwargs] = {}
    for hook in hooks:
        method_data[hook.id] = webhook_settings.CLIENT_KWARGS(hook)
        method_data[hook.id].setdefault("headers", {})
        method_data[hook.id]["headers"].update(hook.default_headers())
        method_data[hook.id]["json"] = data

    asyncio.run(fire_webhooks(hooks, method_data))


def default_post_delete_handler(ref: str, data: JSONData) -> None:
    webhook_model = get_webhookhook_model()

    signal_types = SignalChoices.delete_choises()
    hooks = webhook_model.objects.get_for_ref(ref, signals=signal_types)

    if not hooks.exists():
        return

    method_data: Dict[int, ClientMethodKwargs] = {}
    for hook in hooks:
        method_data[hook.id] = webhook_settings.CLIENT_KWARGS(hook)
        method_data[hook.id].setdefault("headers", {})
        method_data[hook.id]["headers"].update(hook.default_headers())
        method_data[hook.id]["json"] = data

    asyncio.run(fire_webhooks(hooks, method_data))


async def fire_webhooks(hooks: QuerySet["Webhook"], method_data: Dict[int, ClientMethodKwargs]) -> None:
    futures: Set[asyncio.Task] = set()
    hooks_by_name: Dict[str, "Webhook"] = {hook.name: hook for hook in hooks}
    webhook_model = get_webhookhook_model()

    async with httpx.AsyncClient(timeout=webhook_settings.TIMEOUT, follow_redirects=True) as client:
        for hook in hooks:
            futures.add(asyncio.Task(client.post(hook.endpoint, **method_data[hook.id]), name=hook.name))

        async for task in tasks_as_completed(futures):
            hook = hooks_by_name[task.get_name()]

            try:
                response: httpx.Response = task.result()
            except Exception as error:  # pylint: disable=broad-except
                logger.exception(f"Webhook {hook.name!r} failed.", exc_info=error)
                hook.last_failure = datetime.now(tz=timezone.utc)
                webhook_settings.ERROR_HANDLER(hook, error)
                continue

            if response.status_code // 100 == 2:
                hook.last_success = datetime.now(tz=timezone.utc)
                if hook.keep_last_response:
                    hook.last_response = truncate(response.content.decode())

            else:
                hook.last_failure = datetime.now(tz=timezone.utc)
                webhook_settings.ERROR_HANDLER(hook, None)
                if hook.keep_last_response:
                    hook.last_response = truncate(response.content.decode())

    await sync_to_async(webhook_model.objects.bulk_update)(
        objs=hooks,
        fields=[
            "last_success",
            "last_failure",
            "last_response",
        ],
    )

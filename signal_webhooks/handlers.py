from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from threading import Thread
from typing import TYPE_CHECKING

import httpx
from asgiref.sync import sync_to_async
from django.db.models import Model, QuerySet, signals
from django.dispatch import receiver

from .exceptions import WebhookCancelled
from .settings import webhook_settings
from .utils import get_webhookhook_model, reference_for_model, tasks_as_completed, truncate

if TYPE_CHECKING:
    from django.db.models.base import ModelBase

    from .models import Webhook
    from .typing import (
        Any,
        Callable,
        ClientKwargs,
        Dict,
        HooksData,
        JSONData,
        Method,
        Optional,
        PostDeleteData,
        PostSaveData,
        Set,
    )


__all__ = [
    "default_error_handler",
    "default_hook_handler",
    "sync_task_handler",
    "thread_task_handler",
    "webhook_delete_handler",
    "webhook_update_create_handler",
]


logger = logging.getLogger(__name__)


@receiver(signals.post_save, dispatch_uid=webhook_settings.DISPATCH_UID_POST_SAVE)
def webhook_update_create_handler(sender: ModelBase, **kwargs: Any) -> None:
    kwargs: PostSaveData
    webhook_handler(instance=kwargs["instance"], method="CREATE" if kwargs["created"] else "UPDATE")


@receiver(signals.post_delete, dispatch_uid=webhook_settings.DISPATCH_UID_POST_DELETE)
def webhook_delete_handler(sender: ModelBase, **kwargs: Any) -> None:
    kwargs: PostDeleteData
    webhook_handler(instance=kwargs["instance"], method="DELETE")


def webhook_handler(instance: Model, method: Method) -> None:
    ref = reference_for_model(type(instance))

    hook = find_hook_handler(ref, method)
    if hook is None:
        return

    try:
        data = webhook_settings.SERIALIZER(instance)
    except WebhookCancelled as error:
        logger.info(f"{method.capitalize()} webhook for {ref!r} cancelled before it was sent. Reason given: {error}")
        return
    except Exception as error:
        logger.exception(
            f"{method.capitalize()} webhook data for {ref!r} could not be created.",
            exc_info=error,
        )
        return

    webhook_settings.TASK_HANDLER(hook, instance=instance, data=data, method=method)


def find_hook_handler(ref: str, method: Method) -> Optional[Callable]:
    hook: Optional[Callable] = ...
    hooks: Optional[HooksData] = webhook_settings.HOOKS.get(ref)

    if hooks is None:
        return None
    if hooks is not ...:
        hook = hooks.get(method)
    if hook is None:
        return None
    if hook is ...:
        hook = default_hook_handler

    return hook


def default_error_handler(hook: Webhook, error: Optional[Exception]) -> None:
    """
    Default handler for errors from webhooks.

    :param hook: Hook that failed
    :param error: Exception if one was caused due to, e.g., timeout.
    """


def thread_task_handler(hook: Callable[..., None], **kwargs: Any) -> None:
    thread = Thread(target=hook, kwargs=kwargs)
    thread.start()


def sync_task_handler(hook: Callable[..., None], **kwargs: Any) -> None:
    hook(**kwargs)


def default_hook_handler(instance: Model, data: JSONData, method: Method) -> None:
    hooks: QuerySet[Webhook] = get_webhookhook_model().objects.get_for_model(instance, method=method)
    if not hooks.exists():
        return

    client_kwargs = build_client_kwargs_by_hook_id(hooks)
    asyncio.run(fire_webhooks(hooks, data, client_kwargs))


def build_client_kwargs_by_hook_id(
    hooks: QuerySet[Webhook],
) -> Dict[int, ClientKwargs]:
    client_kwargs_by_hook_id: Dict[int, ClientKwargs] = {}
    for hook in hooks:
        client_kwargs_by_hook_id[hook.id] = webhook_settings.CLIENT_KWARGS(hook)
        client_kwargs_by_hook_id[hook.id].setdefault("headers", {})
        client_kwargs_by_hook_id[hook.id]["headers"].update(hook.default_headers())
    return client_kwargs_by_hook_id


async def fire_webhooks(hooks: QuerySet[Webhook], data: JSONData, client_kwargs: Dict[int, ClientKwargs]) -> None:
    futures: Set[asyncio.Task] = set()
    hooks_by_name: Dict[str, Webhook] = {hook.name: hook for hook in hooks}
    webhook_model = get_webhookhook_model()

    async with httpx.AsyncClient(timeout=webhook_settings.TIMEOUT, follow_redirects=True) as client:
        for hook in hooks:
            futures.add(
                asyncio.Task(
                    client.post(hook.endpoint, json=data, **client_kwargs[hook.id]),
                    name=hook.name,
                )
            )

        async for task in tasks_as_completed(futures):
            hook = hooks_by_name[task.get_name()]

            try:
                response: httpx.Response = task.result()
            except Exception as error:
                logger.exception(f"Webhook {hook.name!r} failed.", exc_info=error)
                hook.last_failure = datetime.now(tz=timezone.utc)
                webhook_settings.ERROR_HANDLER(hook, error)
                continue

            if response.status_code // 100 == 2:  # noqa: PLR2004
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

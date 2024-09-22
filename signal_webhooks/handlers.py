from __future__ import annotations

import asyncio
import datetime
import logging
from threading import Thread
from typing import TYPE_CHECKING

import httpx
from asgiref.sync import sync_to_async
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .exceptions import WebhookCancelled
from .settings import webhook_settings
from .typing import ACTION_TO_METHOD
from .utils import get_webhook_model, reference_for_model, tasks_as_completed, truncate

if TYPE_CHECKING:
    from django.db.models.base import ModelBase

    from .models import Webhook
    from .typing import (
        Any,
        Callable,
        ClientKwargs,
        HooksData,
        JSONData,
        M2MChangedData,
        Method,
        PostDeleteData,
        PostSaveData,
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


@receiver(post_save, dispatch_uid=webhook_settings.DISPATCH_UID_POST_SAVE)
def webhook_update_create_handler(sender: ModelBase, **kwargs: Any) -> None:  # noqa: ARG001
    kwargs: PostSaveData
    method: Method = "CREATE" if kwargs["created"] else "UPDATE"  # type: ignore[assignment]
    webhook_handler(instance=kwargs["instance"], method=method)


@receiver(post_delete, dispatch_uid=webhook_settings.DISPATCH_UID_POST_DELETE)
def webhook_delete_handler(sender: ModelBase, **kwargs: Any) -> None:  # noqa: ARG001
    kwargs: PostDeleteData
    method: Method = "DELETE"
    webhook_handler(instance=kwargs["instance"], method=method)


@receiver(models.signals.m2m_changed, dispatch_uid=webhook_settings.DISPATCH_UID_M2M_CHANGED)
def webhook_m2m_handler(sender: ModelBase, **kwargs: Any) -> None:  # noqa: ARG001
    kwargs: M2MChangedData
    method: Method | None = ACTION_TO_METHOD.get(kwargs["action"])
    # Don't fire webhooks for pre-actions
    if method is None:
        return
    webhook_handler(instance=kwargs["instance"], method=method)


def webhook_handler(instance: models.Model, method: Method) -> None:
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


def find_hook_handler(ref: str, method: Method) -> Callable | None:
    hook: Callable | None = ...
    hooks: HooksData | None = webhook_settings.HOOKS.get(ref)

    if hooks is None:
        return None
    if hooks is not ...:
        hook = hooks.get(method)
    if hook is None:
        return None
    if hook is ...:
        hook = default_hook_handler

    return hook


def default_error_handler(hook: Webhook, error: Exception | None) -> None:
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


def default_hook_handler(instance: models.Model, data: JSONData, method: Method) -> None:
    hooks: models.QuerySet = get_webhook_model().objects.get_for_model(instance, method=method)
    if not hooks.exists():
        return

    client_kwargs = build_client_kwargs_by_hook_id(hooks)
    asyncio.run(fire_webhooks(hooks, data, client_kwargs))


def build_client_kwargs_by_hook_id(hooks: models.QuerySet) -> dict[int, ClientKwargs]:
    client_kwargs_by_hook_id: dict[int, ClientKwargs] = {}
    for hook in hooks:
        client_kwargs_by_hook_id[hook.id] = webhook_settings.CLIENT_KWARGS(hook)
        client_kwargs_by_hook_id[hook.id].setdefault("headers", {})
        client_kwargs_by_hook_id[hook.id]["headers"].update(hook.default_headers())
    return client_kwargs_by_hook_id


async def fire_webhooks(hooks: models.QuerySet, data: JSONData, client_kwargs: dict[int, ClientKwargs]) -> None:
    futures: set[asyncio.Task] = set()
    hooks_by_name: dict[str, Webhook] = {hook.name: hook for hook in hooks}
    webhook_model = get_webhook_model()

    async with httpx.AsyncClient(timeout=webhook_settings.TIMEOUT, follow_redirects=True) as client:
        futures.update(
            asyncio.Task(
                client.post(hook.endpoint, json=data, **client_kwargs[hook.id]),
                name=hook.name,
            )
            for hook in hooks
        )

        async for task in tasks_as_completed(futures):
            hook = hooks_by_name[task.get_name()]

            try:
                response: httpx.Response = task.result()
            except Exception as error:
                logger.exception(f"Webhook {hook.name!r} failed.", exc_info=error)
                hook.last_failure = datetime.datetime.now(tz=datetime.timezone.utc)
                webhook_settings.ERROR_HANDLER(hook, error)
                continue

            if response.status_code // 100 == 2:  # noqa: PLR2004
                hook.last_success = datetime.datetime.now(tz=datetime.timezone.utc)
                if hook.keep_last_response:
                    hook.last_response = truncate(response.content.decode())

            else:
                hook.last_failure = datetime.datetime.now(tz=datetime.timezone.utc)
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

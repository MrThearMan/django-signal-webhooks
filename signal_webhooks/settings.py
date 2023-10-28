from __future__ import annotations

from django.test.signals import setting_changed
from settings_holder import SettingsHolder, reload_settings

from .typing import Any, Dict, HooksData, Method, NamedTuple, Optional, Set, Union

__all__ = [
    "webhook_settings",
]


class DefaultSettings(NamedTuple):
    #
    # Defines hooks for models. Key in the dict is the dot import path for a model,
    # e.g., "django.contrib.auth.models.User", and the value for a key defines that
    # model's hooks. Setting the value (or any of value for the keys in 'HooksData')
    # to ... (ellipses) will use the default handlers for the model (or appropriate
    # signal from 'HooksData' key). Setting the value (or any of value for the keys in
    # 'HooksData') to None will explicitly not allow hooks for that model (or appropriate
    # signal from 'HooksData' key). Webhooks cannot be created without the appropriate
    # definition in this setting.
    HOOKS: Dict[str, Optional[HooksData]] = {}
    #
    # Timeout for responses from webhooks before they fail.
    TIMEOUT: int = 10
    #
    # Cipher key to use when encrypting tokens into the database.
    # Should be 16, 24, or 32 bytes converted to base64. You can use
    # 'signal_webhooks.utils.random_cipher_key' to generate one.
    CIPHER_KEY: Optional[str] = None
    #
    # When this is set to True, auth_token will be hidden in admin panel after
    # it has been set. A small snippet from the end of the code will be shown
    # in the helptext for the field. Saving the model again without adding another
    # token will reuse the hidden token.
    HIDE_TOKEN: bool = False
    #
    # Default serializer function to use for serializing model to json-acceptable
    # data. Takes these arguments (instance: Model), and should return
    # data matching 'signal_webhooks.typing.JSONData'.
    #
    # Can also be overridden on per-model basis by declaring a 'webhook_data'
    # method on the model. This function takes no arguments, and should return
    # data matching 'signal_webhooks.typing.JSONData'.
    SERIALIZER: str = "signal_webhooks.utils.default_serializer"
    #
    # Hook for adding additional arguments for the http client that sends the webhooks.
    # Takes these arguments (hook: Webhook), and should return data matching
    # 'signal_webhooks.typing.ClientKwargs'. Note that the headers from the hook will be
    # updated to the 'headers' argument, and the data sent by the webhook will be in json form.
    CLIENT_KWARGS: str = "signal_webhooks.utils.default_client_kwargs"
    #
    # Hook for adding additional filtering to the database query when selecting hooks to fire.
    # Takes these arguments (instance: Model, method: Literal['CREATE', 'UPDATE', 'DELETE']),
    # and should return a dict with the additional arguments passed to 'QuerySet.filter()'.
    # See 'signal_webhooks.models.WebhookQuerySet.get_for_model' for the filtering arguments
    # that are already added by default.
    FILTER_KWARGS: str = "signal_webhooks.utils.default_filter_kwargs"
    #
    # Error handing function that will be called if a webhook fails. Takes these
    # arguments (hook: Webhook, error: Optional[Exception]) and returns None.
    # "error" will be given if the webhook timed out, or a response from the
    # client could not otherwise be created. Note, that the handler will be run
    # inside an async event loop, so 'asgiref.sync_to_async' should be used for
    # any database calls.
    ERROR_HANDLER: str = "signal_webhooks.handlers.default_error_handler"
    #
    # Function that starts the hook once it has been found. Takes these arguments
    # (hook: Callable[..., None], **kwargs: Any) and returns None. The default handler
    # starts a thread that calls the hook with the given kwargs.
    TASK_HANDLER: str = "signal_webhooks.handlers.thread_task_handler"
    #
    # Unique id for the 'signals.post_save' receiver the webhooks are using.
    DISPATCH_UID_POST_SAVE: str = "django-signal-webhooks-post-save"
    #
    # Unique id for the 'signals.post_delete' receiver the webhooks are using.
    DISPATCH_UID_POST_DELETE: str = "django-signal-webhooks-post-delete"


SETTING_NAME: str = "SIGNAL_WEBHOOKS"

DEFAULTS = DefaultSettings()._asdict()

IMPORT_STRINGS: Set[Union[bytes, str]] = {
    "HOOKS",
    "SERIALIZER",
    "CLIENT_KWARGS",
    "FILTER_KWARGS",
    "ERROR_HANDLER",
    "TASK_HANDLER",
}

REMOVED_SETTINGS: Set[str] = set()


class WebhookSettingsHolder(SettingsHolder):
    def perform_import(self, val: Any, setting: str) -> Any:
        if setting not in {"HOOKS"}:
            return super().perform_import(val, setting)  # pragma: no cover

        val: Dict[str, HooksData]
        method: Method
        for model_path, webhooks in val.items():
            if webhooks in (..., None):
                continue

            for method, func_path in webhooks.items():
                if func_path in (..., None):
                    continue

                val[model_path][method] = self.import_from_string(func_path, setting)

        return val


webhook_settings = WebhookSettingsHolder(
    setting_name=SETTING_NAME,
    defaults=DEFAULTS,
    import_strings=IMPORT_STRINGS,
    removed_settings=REMOVED_SETTINGS,
)

reload_my_settings = reload_settings(SETTING_NAME, webhook_settings)
setting_changed.connect(reload_my_settings)

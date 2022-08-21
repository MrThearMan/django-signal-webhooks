import logging

from django import forms
from django.contrib import admin

from .settings import webhook_settings
from .typing import Optional
from .utils import get_webhookhook_model


__all__ = [
    "WebhookModelForm",
    "WebhookAdmin",
]


logger = logging.getLogger(__name__)


WebhookModel = get_webhookhook_model()


class WebhookModelForm(forms.ModelForm):
    class Meta:
        model = WebhookModel
        fields = "__all__"
        widgets = {
            "auth_token": forms.Textarea,
        }

    def __init__(self, *args, **kwargs):
        if webhook_settings.HIDE_TOKEN:
            instance: Optional[WebhookModel] = kwargs.get("instance")
            self._auth_token: Optional[str] = None
            if instance is not None:
                self._auth_token = instance.auth_token
                instance.auth_token = ""

        super().__init__(*args, **kwargs)

        if webhook_settings.HIDE_TOKEN:
            if self._auth_token is not None:
                masked_auth_token = self._auth_token.replace(self._auth_token[:-5], "********", 1)
                self.fields["auth_token"].help_text += f" Current token: {masked_auth_token}"

    def clean(self):
        if webhook_settings.HIDE_TOKEN:
            if self.cleaned_data["auth_token"] == "" and self._auth_token is not None:
                self.cleaned_data["auth_token"] = self._auth_token
        return super().clean()


@admin.register(WebhookModel)
class WebhookAdmin(admin.ModelAdmin):
    form = WebhookModelForm
    list_display = [
        "name",
        "ref",
        "endpoint",
        "last_success",
        "last_failure",
        "enabled",
    ]
    list_filter = [
        "ref",
        "enabled",
        "signal",
    ]
    search_fields = [
        "name",
        "ref",
        "endpoint",
        "last_response",
    ]
    readonly_fields = [
        "last_response",
        "last_success",
        "last_failure",
    ]

    def lookup_allowed(self, lookup, value):  # pragma: no cover
        # Don't allow lookups involving auth tokens
        return not lookup.startswith("auth_token") and super().lookup_allowed(lookup, value)

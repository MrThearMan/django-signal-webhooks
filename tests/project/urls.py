# ruff: noqa
import json
from contextlib import suppress

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.core.management import call_command
from django.http import JsonResponse
from django.urls import include, path
from django.views import View
from rest_framework.routers import DefaultRouter

from signal_webhooks.api.views import WebhooksViewSet

with suppress(Exception):
    call_command("makemigrations")
    call_command("migrate")
    if not User.objects.filter(username="x", email="user@user.com").exists():
        User.objects.create_superuser(username="x", email="user@user.com", password="x")


class WebhookTestView(View):
    """This view is for testing webhooks with ngrok locally."""

    def post(self, request: WSGIRequest, *args, **kwargs):
        print(json.dumps(json.loads(request.body.decode()), indent=2))
        return JsonResponse({"response": "ok"}, status=200)


router = DefaultRouter()
router.register(r"webhook", WebhooksViewSet, basename="webhook")

urlpatterns = [
    path("", include(router.urls)),
    path("hook/", WebhookTestView.as_view(), name="hook"),
    path("admin/", admin.site.urls),
]

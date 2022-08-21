import json
from contextlib import suppress

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.core.management import call_command
from django.http import JsonResponse
from django.urls import path
from django.views import View


with suppress(Exception):
    call_command("makemigrations")
    call_command("migrate")
    if not User.objects.filter(username="x", email="user@user.com").exists():
        User.objects.create_superuser(username="x", email="user@user.com", password="x")


class WebhookTestView(View):
    """This view is for testing webhooks with ngrok locally."""

    def post(self, request: WSGIRequest, *args, **kwargs):
        print(request.body.decode())
        print(json.dumps(json.loads(request.body.decode()), indent=2))
        return JsonResponse({"response": "ok"}, status=200)


urlpatterns = [
    path("hook/", WebhookTestView.as_view(), name="hook"),
    path("admin/", admin.site.urls),
]

from django.apps import AppConfig

__all__ = [
    "MyAppConfig",
]


class MyAppConfig(AppConfig):
    name = "tests.my_app"
    verbose_name = "My App"
    default_auto_field = "django.db.models.BigAutoField"

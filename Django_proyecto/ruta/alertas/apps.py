from django.apps import AppConfig


class AlertasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "alertas"

    def ready(self):
        from . import signals  # noqa: F401  (conecta la difusión de alertas al chat)

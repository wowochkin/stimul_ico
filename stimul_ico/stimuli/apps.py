from django.apps import AppConfig


class StimuliConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stimuli'
    verbose_name = 'Стимулирующие выплаты'

    def ready(self):
        from . import signals  # noqa: F401

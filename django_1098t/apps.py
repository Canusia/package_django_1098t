# django_1098t/apps.py

from django.apps import AppConfig


class Django1098TConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_1098t'
    verbose_name = 'IRS Form 1098-T'
    
    def ready(self):
        """Import signals and perform app initialization."""
        pass
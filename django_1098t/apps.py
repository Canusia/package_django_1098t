# webapp/django_1098t/django_1098t/apps.py

import os
from django.apps import AppConfig


class Django1098TConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_1098t'
    verbose_name = 'IRS Form 1098-T'
    

    CONFIGURATORS = [
        {
            'app': 'django_1098t',
            'name': 'f1098',
            'title': '1098 Settings',
            'description': '-',
            'categories': [
                '1'
            ]
        },
    ]

    REPORTS = [
        {
            'app': 'django_1098t',
            'name': 'f1098_data_export',
            'title': '1098 Student Data Export',
            'description': 'Export student data used in 1098T',
            'categories': [
                'Students'
            ],
            'available_for': [
                'ce'
            ]
        },
        {
            'app': 'django_1098t',
            'name': 'filled_form1098',
            'title': 'Filled 1098 Tax Form(s)',
            'description': 'Generate filled 1098Ts',
            'categories': [
                'Students'
            ],
            'available_for': [
                'ce'
            ]
        },
    ]

    # Dynamically set the correct path
    path = os.path.dirname(os.path.abspath(__file__))
    
    def ready(self):
        """Import signals and perform app initialization."""
        pass


class DevDjango1098TConfig(AppConfig):
    """Development app config - when using as submodule."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_1098t.django_1098t'
    verbose_name = 'Dev - IRS Form 1098-T'
    
    def ready(self):
        """Import signals and perform app initialization."""
        pass
    
# webapp/django_1098t/django_1098t/constants.py

import os
from django.conf import settings

# Storage settings
STORAGE_PATH_PREFIX = 'tax_forms/1098t/'


def get_filer_info():
    """
    Get filer information from Setting model.
    
    Returns:
        dict with keys: name, ein, address, phone
    """
    try:
        from .settings.f1098 import f1098 as f1098_setting
        configs = f1098_setting.from_db()

        return {
            'name': configs.get('school_name'),
            'ein': configs.get('school_ein'),
            'address': configs.get('school_address'),
            'phone': configs.get('school_phone', ' '),
            'service_provider_account': configs.get('service_provider_account', '')  # Add this
        }
    except Exception as e:
        print(f"Warning: Could not load filer info from database: {e}")
        return {
            'name': getattr(settings, 'FORM_1098T_FILER_NAME', 'Your University Name'),
            'ein': getattr(settings, 'FORM_1098T_FILER_EIN', '12-3456789'),
            'address': getattr(settings, 'FORM_1098T_FILER_ADDRESS', '123 University Ave'),
            'phone': getattr(settings, 'FORM_1098T_FILER_PHONE', '555-123-4567'),
            'service_provider_account': '',  # Default to empty
        }


def get_template_path(tax_year):
    """Get the PDF template path for a given tax year."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    template_filename = f"{tax_year}.pdf"
    template_path = os.path.join(
        app_dir,
        'templates_pdf',
        'f1098t',
        template_filename
    )
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Template for {tax_year} not found at {template_path}. "
            f"Please add the PDF template to django_1098t/templates_pdf/f1098t/{template_filename}"
        )
    
    return template_path
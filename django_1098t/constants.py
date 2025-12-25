# django_1098t/constants.py

import os
from django.conf import settings

# Filer information (your institution)
FILER_NAME = getattr(settings, 'FORM_1098T_FILER_NAME', 'Your University Name')
FILER_EIN = getattr(settings, 'FORM_1098T_FILER_EIN', '12-3456789')
FILER_ADDRESS = getattr(settings, 'FORM_1098T_FILER_ADDRESS', '123 University Ave, City, ST 12345')
FILER_PHONE = getattr(settings, 'FORM_1098T_FILER_PHONE', '555-123-4567')

# Storage settings
STORAGE_PATH_PREFIX = 'tax_forms/1098t/'


def get_template_path(tax_year):
    """Get the PDF template path for a given tax year."""
    # Get the app directory
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
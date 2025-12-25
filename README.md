# Django 1098-T

A Django app for generating and managing IRS Form 1098-T (Tuition Statement) tax documents.

## Features

- Generate 1098-T forms from student transaction data
- Publish forms individually or in bulk
- Student download portal with authentication
- Download tracking and analytics
- Admin interface for form management
- PDF template support for different tax years
- S3-compatible storage backend

## Requirements

- Python 3.8+
- Django 3.2+
- pypdf 4.0+

## Installation

### Via Git Submodule (Development)
```bash
# In your Django project root
git submodule add https://github.com/yourusername/django-1098t.git
git submodule update --init --recursive

# Install in development mode
pip install -e ./django_1098t
```

### Via pip (When Published)
```bash
pip install django-1098t
```

## Configuration

### 1. Add to INSTALLED_APPS
```python
# settings.py

INSTALLED_APPS = [
    # ...
    'django_1098t',
]
```

### 2. Configure Settings
```python
# settings.py

# Filer Information (Your Institution)
FORM_1098T_FILER_NAME = 'Your University Name'
FORM_1098T_FILER_EIN = '12-3456789'
FORM_1098T_FILER_ADDRESS = '123 University Ave, City, ST 12345'
FORM_1098T_FILER_PHONE = '555-123-4567'
```

### 3. Include URLs
```python
# urls.py

urlpatterns = [
    # ...
    path('tax-forms/', include('django_1098t.urls')),
]
```

### 4. Run Migrations
```bash
python manage.py migrate django_1098t
```

### 5. Add PDF Templates

Place your IRS Form 1098-T PDF templates in:
```
django_1098t/templates_pdf/f1098t/
├── 2024.pdf
├── 2025.pdf
└── 2026.pdf
```

## Usage

### Publishing Forms

#### Via Management Command
```bash
# Publish forms for all students for 2024
python manage.py publish_1098t 2024

# Publish for a specific student
python manage.py publish_1098t 2024 --student-id 123

# Regenerate existing forms
python manage.py publish_1098t 2024 --regenerate
```

#### Via Admin Interface

Navigate to `/tax-forms/admin/publish/` to access the publishing interface.

### Student Access

Students can access their forms at `/tax-forms/my-forms/`

### Admin Features

- Bulk publishing: `/tax-forms/admin/publish/`
- Download statistics: `/tax-forms/admin/statistics/`
- Bulk download: `/tax-forms/admin/bulk-download/<year>/`
- Django admin: `/admin/django_1098t/`

## Required Models

This package expects the following models to exist in your Django project:

### Student Model
```python
# Expected at: cis.models.student.Student
# With relation to User model via student.user
```

### StudentTransaction Model
```python
# Expected at: student_transactions.models.StudentTransaction
# Must have: student, created_on, t_type, label, amount fields
# Must implement: get_bulk_1098t_summary() manager method
```

### Storage Backend
```python
# Expected at: cis.backends.storage_backend.PrivateMediaStorage
# Compatible with django-storages S3 backend
```

## Customization

### Custom Storage Backend
```python
# In your settings.py
DJANGO_1098T_STORAGE_CLASS = 'myapp.backends.CustomStorage'
```

### Custom Templates

Override the default templates by creating files in your project:
```
templates/django_1098t/
├── student_forms_list.html
├── admin_publish.html
└── admin_statistics.html
```

## API Reference

### Services

#### Form1098TPublisher
```python
from django_1098t.services.publisher import Form1098TPublisher

publisher = Form1098TPublisher(tax_year=2024, published_by=user)

# Publish for all students
results = publisher.publish_all_students()

# Publish for one student
result = publisher.publish_student_form(student, regenerate=True)
```

#### Form1098TGenerator
```python
from django_1098t.services.generator import Form1098TGenerator

generator = Form1098TGenerator(template_path='/path/to/template.pdf')

pdf_bytes = generator.generate_filled_form(
    student_data={...},
    amounts={...}
)
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please use the GitHub issue tracker.
```

### .gitignore
```
# .gitignore

# Python
*.py[cod]
*$py.class
*.so
__pycache__/
*.egg-info/
dist/
build/
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Package
django_1098t.egg-info/
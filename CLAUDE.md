# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Django 1098-T is a reusable Django app for generating and managing IRS Form 1098-T tax documents. It provides PDF generation, student download portal, admin publishing interface, and download analytics.

## Commands

```bash
# Run migrations
python manage.py migrate django_1098t

# Publish 1098-T forms for all students
python manage.py publish_1098t <tax_year>

# Publish for specific student
python manage.py publish_1098t <tax_year> --student-id <id>

# Regenerate existing forms
python manage.py publish_1098t <tax_year> --regenerate

# Inspect PDF template fields (debug utility)
python manage.py inspect_1098t_template <year> --show-types --show-values

# Test PDF generation with sample data
python manage.py test_1098t_generation <year> --output <filename>

# Run tests
python -m pytest tests/

# Run a single test file
python -m pytest tests/test_generator.py

# Run a single test function
python -m pytest tests/test_generator.py::test_function_name -v
```

## Architecture

### Core Services (`django_1098t/services/`)

- **generator.py**: `Form1098TGenerator` - Fills PDF templates using pypdf, returns BytesIO
- **publisher.py**: `Form1098TPublisher` - Orchestrates publishing workflow (fetch transactions → generate PDF → store to S3 → create DB record)
- **storage.py**: `Form1098TStorage` - S3 storage abstraction using `PrivateMediaStorage`, path prefix: `tax_forms/1098t/`

### Models (`django_1098t/models.py`)

- **Form1098T**: Stores generated forms with denormalized financial data, student info snapshot, S3 file path, publishing metadata. Unique constraint: one published form per student per tax year.
- **Form1098TDownload**: Tracks download analytics (IP, user agent, timestamps) for compliance.

### Views (`django_1098t/views/`)

- **admin_views.py**: Staff-only - bulk publishing, download statistics, ZIP export, DataTables list
- **student_views.py**: Student portal - form list, secure download with access control
- **api_views.py**: Read-only DRF viewset with DataTables support

### Reports (`django_1098t/reports/`)

Contains report generation logic for 1098-T form analytics and exports.

### External Dependencies

The app expects these models from the parent project:
- `cis.models.student.Student` - Student model with `student.user` relation
- `cis.models.customuser.CustomUser` - User model
- `student_transactions.models.StudentTransaction` - Must implement `get_bulk_1098t_summary()` manager method
- `cis.backends.storage_backend.PrivateMediaStorage` - S3-compatible storage

### PDF Templates

Located in `django_1098t/templates_pdf/f1098t/` with naming convention `{year}.pdf` (e.g., 2025.pdf).

### Configuration

School info (name, EIN, address, phone) configured via database settings in `django_1098t/settings/f1098.py`. Transaction type filters also configurable.

Django settings (in parent project's `settings.py`):
```python
FORM_1098T_FILER_NAME = 'Your University Name'
FORM_1098T_FILER_EIN = '12-3456789'
FORM_1098T_FILER_ADDRESS = '123 University Ave, City, ST 12345'
FORM_1098T_FILER_PHONE = '555-123-4567'
```

## URL Namespace

All URLs use namespace `django_1098t`:
- Student: `my-forms/`, `download/<form_id>/`
- Admin: `admin/publish/`, `admin/statistics/`, `admin/bulk-download/<year>/`, `1098t/list/`
- API: `/api/forms` via DRF router

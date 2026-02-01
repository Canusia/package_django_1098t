# webapp/django_1098t/django_1098t/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.student_views import download_form, student_forms_list, submit_consent
from .views.admin_views import (
    publish_forms_view,
    download_statistics_view,
    bulk_download_forms,
    form_1098t_list_view  # Add this
)
from .views.api_views import Form1098TViewSet

app_name = 'django_1098t'

# DRF Router
router = DefaultRouter()
router.register(r'api/forms', Form1098TViewSet, basename='form1098t')

urlpatterns = [
    # Student URLs
    path('my-forms/', student_forms_list, name='student_forms_list'),
    path('download/<uuid:form_id>/', download_form, name='download_form'),
    path('consent/', submit_consent, name='submit_consent'),
    
    # Admin URLs
    path('1098t/list/', form_1098t_list_view, name='admin_list'),  # Add this
    path('admin/publish/', publish_forms_view, name='admin_publish'),
    path('admin/statistics/', download_statistics_view, name='admin_statistics'),
    path('admin/bulk-download/<int:tax_year>/', bulk_download_forms, name='bulk_download'),
    
    # API URLs
    path('', include(router.urls)),
]
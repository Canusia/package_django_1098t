# django_1098t/urls.py

from django.urls import path
from django_1098t.views import student_views, admin_views

app_name = 'django_1098t'

urlpatterns = [
    # Student URLs
    path('my-forms/', student_views.student_forms_list, name='student_forms_list'),
    path('download/<uuid:form_id>/', student_views.download_form, name='download_form'),
    
    # Admin URLs
    path('admin/publish/', admin_views.publish_forms_view, name='admin_publish'),
    path('admin/statistics/', admin_views.download_statistics_view, name='admin_statistics'),
    path('admin/bulk-download/<int:tax_year>/', admin_views.bulk_download_forms, name='bulk_download'),
]
# django_1098t/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Form1098T, Form1098TDownload


@admin.register(Form1098T)
class Form1098TAdmin(admin.ModelAdmin):
    list_display = [
        'student_name',
        'tax_year',
        'is_published',
        'payments_received',
        'scholarships_grants',
        'download_count_display',
        'published_at',
        'actions_column'
    ]
    list_filter = ['tax_year', 'is_published', 'published_at']
    search_fields = ['student_name', 'student__user__email', 'student_tin']
    readonly_fields = [
        'created_at',
        'updated_at',
        'file_size',
        'download_count_display',
        'last_downloaded_display'
    ]
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'student_name', 'student_tin', 'student_address')
        }),
        ('Tax Information', {
            'fields': (
                'tax_year',
                'payments_received',
                'scholarships_grants',
                'adjustments',
                'scholarship_adjustments'
            )
        }),
        ('File Details', {
            'fields': ('file_path', 'file_size')
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at', 'published_by')
        }),
        ('Statistics', {
            'fields': ('download_count_display', 'last_downloaded_display')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def download_count_display(self, obj):
        return obj.download_count
    download_count_display.short_description = 'Downloads'
    
    def last_downloaded_display(self, obj):
        return obj.last_downloaded_at or 'Never'
    last_downloaded_display.short_description = 'Last Downloaded'
    
    def actions_column(self, obj):
        if obj.is_published:
            download_url = obj.get_download_url()
            return format_html(
                '<a class="button" href="{}" target="_blank">View PDF</a>',
                download_url
            )
        return '-'
    actions_column.short_description = 'Actions'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('student__user', 'published_by')


@admin.register(Form1098TDownload)
class Form1098TDownloadAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'form_year',
        'downloaded_at',
        'ip_address'
    ]
    list_filter = ['downloaded_at', 'form__tax_year']
    search_fields = ['student__user__email', 'student__user__first_name', 'student__user__last_name']
    readonly_fields = ['form', 'student', 'downloaded_at', 'ip_address', 'user_agent', 'file_path_snapshot']
    
    def form_year(self, obj):
        return obj.form.tax_year
    form_year.short_description = 'Tax Year'
    form_year.admin_order_field = 'form__tax_year'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
# django_1098t/models.py

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from cis.models.student import Student


class Form1098TManager(models.Manager):
    def get_latest_for_student(self, student, tax_year):
        """Get the most recent form for a student and tax year."""
        return self.filter(
            student=student,
            tax_year=tax_year,
            is_published=True
        ).order_by('-published_at').first()
    
    def get_unpublished_count(self, tax_year):
        """Count students with transactions but no published form."""
        from student_transactions.models import StudentTransaction
        
        # Students with transactions in the year
        students_with_transactions = StudentTransaction.objects.filter(
            created_on__year=tax_year
        ).values_list('student_id', flat=True).distinct()
        
        # Students with published forms
        students_with_forms = self.filter(
            tax_year=tax_year,
            is_published=True
        ).values_list('student_id', flat=True).distinct()
        
        return len(set(students_with_transactions) - set(students_with_forms))


class Form1098T(models.Model):
    """
    Stores generated 1098-T tax forms for students.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='form_1098t_records'
    )
    tax_year = models.IntegerField(
        help_text="Calendar year for the tax form (e.g., 2024)"
    )
    
    # Financial data (denormalized for archival purposes)
    payments_received = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Box 1: Payments received for qualified tuition"
    )
    scholarships_grants = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Box 5: Scholarships or grants"
    )
    adjustments = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Box 4: Adjustments made for a prior year"
    )
    scholarship_adjustments = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Box 6: Adjustments to scholarships for a prior year"
    )
    
    # Student info snapshot (for audit trail)
    student_name = models.CharField(max_length=255)
    student_tin = models.CharField(max_length=11, blank=True)
    student_address = models.TextField()
    
    # File storage
    file_path = models.CharField(
        max_length=500,
        help_text="S3 path to the PDF file"
    )
    file_size = models.IntegerField(
        default=0,
        help_text="File size in bytes"
    )
    
    # Publishing metadata
    is_published = models.BooleanField(
        default=False,
        help_text="Whether this form is available for student download"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='published_1098t_forms'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = Form1098TManager()
    
    class Meta:
        db_table = 'form_1098t'
        verbose_name = '1098-T Form'
        verbose_name_plural = '1098-T Forms'
        ordering = ['-tax_year', '-published_at']
        indexes = [
            models.Index(fields=['student', 'tax_year', 'is_published']),
            models.Index(fields=['tax_year', 'is_published']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'tax_year'],
                condition=models.Q(is_published=True),
                name='unique_published_form_per_student_year'
            )
        ]
    
    def __str__(self):
        return f"1098-T {self.tax_year} - {self.student_name}"
    
    @property
    def download_count(self):
        """Total number of times this form has been downloaded."""
        return self.downloads.count()
    
    @property
    def last_downloaded_at(self):
        """Most recent download timestamp."""
        latest = self.downloads.order_by('-downloaded_at').first()
        return latest.downloaded_at if latest else None
    
    def get_download_url(self):
        """Get the Django-proxied download URL (not direct S3)."""
        from django.urls import reverse
        return reverse('django_1098t:download_form', kwargs={'form_id': self.id})


class Form1098TDownload(models.Model):
    """
    Tracks every download of a 1098-T form.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        Form1098T,
        on_delete=models.CASCADE,
        related_name='downloads'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='form_1098t_downloads'
    )
    
    # Download metadata
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # File reference at time of download (for audit)
    file_path_snapshot = models.CharField(max_length=500)
    
    class Meta:
        db_table = 'form_1098t_download'
        verbose_name = '1098-T Download'
        verbose_name_plural = '1098-T Downloads'
        ordering = ['-downloaded_at']
        indexes = [
            models.Index(fields=['form', 'downloaded_at']),
            models.Index(fields=['student', 'downloaded_at']),
        ]
    
    def __str__(self):
        return f"{self.student} downloaded {self.form.tax_year} form at {self.downloaded_at}"
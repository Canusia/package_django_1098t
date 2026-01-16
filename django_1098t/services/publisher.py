# django_1098t/services/publisher.py

from datetime import datetime
from django.db import transaction
from django.utils import timezone
from student_transactions.models import StudentTransaction
from cis.models.student import Student
from ..models import Form1098T
from ..services.generator import Form1098TGenerator
from ..constants import get_template_path
from ..services.storage import Form1098TStorage
from typing import Dict


class Form1098TPublisher:
    """Handles publishing 1098-T forms for students."""
    
    def __init__(self, tax_year: int, published_by):
        self.tax_year = tax_year
        self.published_by = published_by
        self.storage = Form1098TStorage()
        
        # Initialize generator with template for this year
        template_path = get_template_path(tax_year)
        self.generator = Form1098TGenerator(template_path)
    
    def publish_all_students(self, student_ids=None) -> Dict[str, any]:
        """
        Publish 1098-T forms for all eligible students.
        
        Returns:
            Dictionary with success/error counts and details
        """
        if not student_ids:
            # Get all students with transactions in the tax year
            start_date = datetime(self.tax_year, 1, 1)
            end_date = datetime(self.tax_year, 12, 31, 23, 59, 59)
            
            student_ids = StudentTransaction.objects.filter(
                created_on__gte=start_date,
                created_on__lte=end_date
            ).values_list('student__id', flat=True).distinct()
        
        students = Student.objects.filter(
            id__in=student_ids
        ).select_related('user', 'highschool')
        
        results = {
            'success_count': 0,
            'error_count': 0,
            'skipped_count': 0,
            'errors': []
        }
        
        for student in students:
            try:
                result = self.publish_student_form(student)
                if result == 'published':
                    results['success_count'] += 1
                elif result == 'skipped':
                    results['skipped_count'] += 1
            except Exception as e:
                results['error_count'] += 1
                results['errors'].append({
                    'student_id': student.id,
                    'student_name': f"{student.user.first_name} {student.user.last_name}",
                    'error': str(e)
                })
        
        return results
    
    def publish_student_form(self, student: Student, regenerate: bool = True) -> str:
        """
        Publish a 1098-T form for a single student.
        
        Args:
            student: Student object
            regenerate: If True, delete and regenerate existing published forms
            
        Returns:
            'published', 'skipped', or 'error'
        """
        # Get financial summary
        start_date = datetime(self.tax_year, 1, 1)
        end_date = datetime(self.tax_year, 12, 31, 23, 59, 59)
        
        from decimal import Decimal
        from ..settings.f1098 import f1098
        configs = f1098.from_db()

        summary = StudentTransaction.objects.get_bulk_1098t_summary(
            student_ids=[student.id],
            start_date=start_date,
            end_date=end_date,
            configs=configs
        ).get(student.id, {'charges': Decimal('0.0'), 'payments': Decimal('0.0'), 'scholarships': Decimal('0.0')})        

        # Skip if no qualifying transactions
        if summary['payments'] <= 0 and summary['scholarships'] <= 0:
            return 'skipped'
        
        with transaction.atomic():
            # Check for existing published form
            existing_form = Form1098T.objects.filter(
                student=student,
                tax_year=self.tax_year,
                is_published=True
            ).first()
            
            if existing_form:
                if not regenerate:
                    return 'skipped'
                # Delete old file and unpublish
                self.storage.delete_form(existing_form.file_path)
                existing_form.is_published = False
                existing_form.save()
            
            # Generate PDF
            student_data = self._prepare_student_data(student)
            amounts = {
                'payments': summary['payments'],
                'scholarships': summary['scholarships']
            }
            optional_amounts = {
                'adjustments': Decimal('0.0'),
                'scholarship_adjustments': Decimal('0.0'),
                'insurance_refund': Decimal('0.0')
            }
            
            pdf_bytes = self.generator.generate_filled_form(
                student_data=student_data,
                amounts=amounts,
                optional_amounts=optional_amounts
            )
            
            # Save to S3
            file_path, file_size = self.storage.save_form(
                pdf_bytes.getvalue(),
                student.id,
                self.tax_year
            )
            
            # Create database record
            form = Form1098T.objects.create(
                student=student,
                tax_year=self.tax_year,
                payments_received=summary['payments'],
                scholarships_grants=summary['scholarships'],
                adjustments=Decimal('0.0'),
                scholarship_adjustments=Decimal('0.0'),
                student_name=f"{student.user.first_name} {student.user.last_name}",
                student_tin=student.user.ssn or '',
                student_address=self._format_student_address(student),
                file_path=file_path,
                file_size=file_size,
                is_published=True,
                published_at=timezone.now(),
                published_by=self.published_by
            )
            
            return 'published'
    
    def _prepare_student_data(self, student: Student) -> Dict:
        """Prepare student data for PDF generation."""
        user_id = student.user.psid
        if student.user.psid in [None, '', '-']:
            user_id = str(student.id)[:20]
        return {
            'name': f"{student.user.first_name} {student.user.last_name}",
            'tin': student.user.ssn or '',
            'service_provider_account_number': user_id,
            'address': student.user.address1 or '',
            'address2': f"{student.user.city}, {student.user.state} {student.user.postal_code}" if student.user.city else ''
        }
    
    def _format_student_address(self, student: Student) -> str:
        """Format complete student address for storage."""
        parts = [
            student.user.address1,
            student.user.city,
            f"{student.user.state} {student.user.postal_code}"
        ]
        return ", ".join(filter(None, parts))
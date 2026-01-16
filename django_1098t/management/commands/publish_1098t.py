# django_1098t/management/commands/publish_1098t.py

from django.core.management.base import BaseCommand
from ...services.publisher import Form1098TPublisher
from cis.models.customuser import CustomUser


class Command(BaseCommand):
    help = 'Publish 1098-T forms for a tax year'
    
    def add_arguments(self, parser):
        parser.add_argument('tax_year', type=int, help='Tax year (e.g., 2024)')
        parser.add_argument(
            '--student-id',
            type=str,
            help='Publish for specific student only'
        )
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerate existing published forms'
        )
    
    def handle(self, *args, **options):
        tax_year = options['tax_year']
        student_id = options.get('student_id')
        regenerate = options.get('regenerate', False)
        
        # Get a system user for published_by
        system_user = CustomUser.objects.filter(is_superuser=True).first()
        
        if not system_user:
            self.stdout.write(
                self.style.ERROR('No superuser found. Please create one first.')
            )
            return
        
        publisher = Form1098TPublisher(tax_year, system_user)
        
        if student_id:
            from cis.models.student import Student
            try:
                student = Student.objects.get(id=student_id)
                result = publisher.publish_student_form(student, regenerate=regenerate)
                self.stdout.write(
                    self.style.SUCCESS(f'Result for student {student_id}: {result}')
                )
            except Student.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Student with ID {student_id} not found')
                )
        else:
            self.stdout.write(f'Publishing forms for all students for {tax_year}...')
            results = publisher.publish_all_students()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Success: {results['success_count']}, "
                    f"Skipped: {results['skipped_count']}, "
                    f"Errors: {results['error_count']}"
                )
            )
            
            if results['errors']:
                self.stdout.write(self.style.ERROR('\nErrors:'))
                for error in results['errors']:
                    self.stdout.write(f"  - {error['student_name']}: {error['error']}")
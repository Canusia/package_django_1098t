import io, csv, datetime
from django.conf import settings
import os, zipfile
from io import BytesIO
from django import forms
from django.forms import ValidationError
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.db.models import Q, Prefetch
from django.core.files.base import ContentFile
from cis.backends.storage_backend import PrivateMediaStorage
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from cis.models.student import Student
from student_transactions.models import StudentTransaction

from decimal import Decimal
from ..services.generator import Form1098TGenerator
from ..settings.f1098 import f1098 as f1098_settings
from ..constants import get_template_path

class filled_form1098(forms.Form):
    
    created_on_from = forms.DateField(
        widget=forms.DateInput(format='%m/%d/%Y', attrs={'class':'col-md-6 col-sm-12'}),
        required=True,
        label='Transaction Created On From',
        input_formats=[('%m/%d/%Y')]
    )

    created_on_until = forms.DateField(
        widget=forms.DateInput(format='%m/%d/%Y', attrs={'class':'col-md-6 col-sm-12'}),
        required=True,
        label='Transaction Created On Until',
        input_formats=[('%m/%d/%Y')]
    )

    export_type = forms.ChoiceField(
        label='Action',
        choices=[
            ('download', 'Download Zip File'),
            ('publish', 'Publish'),
            # ('push_to_s3', 'Push to S3 Storage'),
        ]
    )

    published_by = forms.CharField(
        required=True,
        widget=forms.HiddenInput
    )
    
    roles = []
    request = None
    
    # add a clean method to make sure the template pdf exists
    def clean(self):
        data = super().clean()

        start_date = data.get('created_on_from')

        try:
            get_template_path(start_date.year)
        except:
            raise ValidationError(f'The PDF template does not exist for {start_date.year}. Please contact the administrator', code='File not found')

        return data
        
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.add_input(Submit('submit', 'Generate Export'))

        if self.request:
            self.helper.form_action = reverse_lazy(
                'report:run_report', args=[request.GET.get('report_id')]
            )

            self.fields['published_by'].initial = self.request.user.id
        
    def get_result(self, data):
        # return [
        #     '484f56ab-0403-42de-b3ae-4c8ef493e364'
        # ]
    
        """Get student IDs with transactions in date range."""
        records = StudentTransaction.objects.filter()

        if data.get('created_on_from')[0]:
            created_from = datetime.datetime.strptime(
                data.get('created_on_from')[0],
                '%m/%d/%Y'
            )
            records = records.filter(created_on__gte=created_from)

        if data.get('created_on_until')[0]:
            created_until = datetime.datetime.strptime(
                data.get('created_on_until')[0],
                '%m/%d/%Y'
            )
            records = records.filter(created_on__lt=created_until)

        return records.values_list('student__id', flat=True).distinct()

    def _generate_student_pdf(self, student, summary, f1098_generator):
        """
        Generate a single student's 1098-T PDF form.
        
        Returns:
            Tuple of (pdf_bytes, filled_form_path) or (None, None) if student has no transactions
        """

        # Skip students with no transactions
        if summary['payments'] <= 0 and summary['scholarships'] <= 0:
            return None, None
        
        user_id = student.user.psid
        if student.user.psid in [None, '', '-']:
            user_id = str(student.id)[:20]
        student_data = {
            'name': f"{student.user.first_name} {student.user.last_name}",
            'tin': student.user.ssn or '',
            'service_provider_account_number': user_id,
            'address': student.user.address1 or '',
            'address2': f"{student.user.city}, {student.user.state} {student.user.postal_code}" if student.user.city else ''
        }
        
        amounts = {
            'payments': summary['payments'],
            'scholarships': summary['scholarships']
        }
        
        optional_amounts = {
            'adjustments': 0.0,
            'scholarship_adjustments': 0.0,
            'insurance_refund': 0.0
        }
        
        filled_form_bytes = f1098_generator.generate_filled_form(
            # filer_data=filer_data,
            student_data=student_data,
            amounts=amounts,
            optional_amounts=optional_amounts
        )
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        filled_form_path = f"f1098t_student_{student.user.last_name}_{student.user.first_name}_{student.user.id}_{timestamp}.pdf"
        
        return filled_form_bytes, filled_form_path

    def _write_csv_row(self, writer, student, summary, filled_form_path):
        """Write a single CSV row for a student."""
        writer.writerow([
            student.id,
            f"{student.user.first_name} {student.user.last_name}",
            student.user.ssn,
            student.user.email,
            student.user.address1,
            student.user.city,
            student.user.state,
            student.user.postal_code,
            student.highschool.name,
            f"{summary['charges']:.2f}",
            f"{summary['scholarships']:.2f}",
            f"{summary['payments']:.2f}",
            filled_form_path
        ])
        
    def run(self, task, data):
        # Parse dates once
        start_date = datetime.datetime.strptime(
            data.get('created_on_from')[0],
            '%m/%d/%Y'
        )
        end_date = datetime.datetime.strptime(
            data.get('created_on_until')[0],
            '%m/%d/%Y'
        )
        
        # Get student IDs
        student_ids = self.get_result(data)
        
        # Optimize: Fetch students with all related data in one query
        students = Student.objects.filter(
            id__in=student_ids
        ).select_related(
            'highschool',
            'user'  # Add this to avoid N+1 queries on user fields
        ).order_by('user__last_name', 'user__first_name')  # Consistent ordering
        
        f1098_configs = f1098_settings.from_db()
        # Get all summaries in one bulk query
        summaries = StudentTransaction.objects.get_bulk_1098t_summary(
            student_ids=student_ids,
            start_date=start_date,
            end_date=end_date,
            configs=f1098_configs
        )

        # Initialize CSV writer
        stream = io.StringIO()
        writer = csv.writer(stream, delimiter=',')
        writer.writerow([
            'Student ID', 'Name', 'ITIN', 
            'Email', 'Address', 'City', 
            'State', 'Zip Code', 'High School', 
            'Qualified Tuition (Box 1)', 
            'Scholarships/Grants (Box 5)',
            'Payments Received (For reference)',
            'Filled 1098-T Form Path'
        ])

        # Initialize PDF generator once
        pdf_template_path = get_template_path(start_date.year)

        f1098_generator = Form1098TGenerator(pdf_template_path)
        
        export_type = data.get('export_type')[0]
        
        filer_data = {
            'name': f1098_configs.get('school_name') + '\r\n' + f1098_configs.get('school_address'),
            'ein': f1098_configs.get('school_ein'),
            'address': ''
        }
        if export_type == 'download':
            return self._handle_download(task, data, students, summaries, f1098_generator, writer, stream)
        elif export_type == 'publish':
            return self._handle_publish(task, data, students, summaries, f1098_generator, writer, stream)
    
    def _handle_download(self, task, form_data, students, summaries, f1098_generator, writer, stream):
        """Handle zip file download export."""
        ZIPFILE_NAME = f"filled_form1098_export_{datetime.datetime.now().strftime('%Y_%m_%d')}.zip"
        b = BytesIO()
        storage = PrivateMediaStorage()
        path_prefix = f'reports/{datetime.datetime.now().strftime("%Y/%m")}/{task.id}/'

        with zipfile.ZipFile(b, 'w', zipfile.ZIP_DEFLATED) as zf:  # Add compression
            for student in students:
                summary = summaries.get(student.id, {
                    'charges': Decimal('0.0'),
                    'payments': Decimal('0.0'),
                    'scholarships': Decimal('0.0')
                })
                
                # Generate PDF
                filled_form_bytes, filled_form_path = self._generate_student_pdf(
                    student, summary, f1098_generator
                )
                
                if filled_form_bytes:  # Only process if student has transactions
                    zf.writestr(filled_form_path, filled_form_bytes.getvalue())
                    self._write_csv_row(writer, student, summary, filled_form_path)
            
            # Write CSV after all students processed
            zf.writestr('tax_form_exports.csv', stream.getvalue())

        # Save to storage and return URL
        response = HttpResponse(b.getvalue(), content_type="application/x-zip-compressed")
        response['Content-Disposition'] = f'attachment; filename={ZIPFILE_NAME}'
        
        path = storage.save(path_prefix + ZIPFILE_NAME, ContentFile(response.getvalue()))
        return storage.url(path)
    
    def _handle_publish(self, task, form_data, students, summaries, f1098_generator, writer, stream):
        """Handle individual file uploads to S3."""
        storage = PrivateMediaStorage()
        timestamp = datetime.datetime.now()
        
        from ..services.publisher import Form1098TPublisher
        start_date = datetime.datetime.strptime(
            form_data.get('created_on_from')[0],
            '%m/%d/%Y'
        )

        # Initialize CSV writer
        stream = io.StringIO()
        writer = csv.writer(stream, delimiter=',')
        writer.writerow([
            'Student ID', 'Name', 'ITIN', 
            'Email', 'Address', 'City', 
            'State', 'Zip Code', 'High School',
            'Result'
        ])

        from cis.models.customuser import CustomUser
        published_by = CustomUser.objects.get(pk=form_data.get('published_by')[0])
        publisher = Form1098TPublisher(start_date.year, published_by)
        
        for student in students:
            result = publisher.publish_student_form(student, True)

            writer.writerow([
                student.id,
                f"{student.user.first_name} {student.user.last_name}",
                student.user.ssn,
                student.user.email,
                student.user.address1,
                student.user.city,
                student.user.state,
                student.user.postal_code,
                student.highschool.name,
                result
            ])
        
        storage = PrivateMediaStorage()
        now = datetime.datetime.now().strftime("%Y/%m")

        file_name = "student-1098t-publish-export.csv"
        path = f"reports/{now}/" + str(task.id) + "/" + file_name
        media_storage = PrivateMediaStorage()

        path = media_storage.save(path, ContentFile(stream.getvalue().encode('utf-8')))
        return path
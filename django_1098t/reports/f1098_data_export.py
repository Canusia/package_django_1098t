import io, csv, datetime

from django import forms
from django.urls import reverse_lazy
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from django.db.models import Sum
from django.core.files.base import ContentFile, File

from cis.backends.storage_backend import PrivateMediaStorage
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from cis.utils import (
    export_to_excel, user_has_cis_role,
    user_has_highschool_admin_role, get_field,
    YES_NO_SELECT_OPTIONS
)

from cis.models.student import Student
from cis.models.highschool_administrator import HSAdministrator
from student_transactions.models import StudentTransaction

from cis.models.term import Term
from cis.models.section import ClassSection, Campus, StudentRegistration

class f1098_data_export(forms.Form):
    
    # start and end date of transactions to include     
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

    roles = []
    request = None
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = request

        self.helper = FormHelper()
        # self.helper.attrs = {'target':'_blank'}
        self.helper.form_method = 'POST'
        self.helper.add_input(Submit('submit', 'Generate Export'))

        # for cis users only show their campus
        if self.request:
            self.helper.form_action = reverse_lazy(
                'report:run_report', args=[request.GET.get('report_id')]
            )
        
    def get_result(self, data):
        term_id = data.get('term')
        
        records = StudentTransaction.objects.filter()

        if data.get('created_on_from')[0]:
            created_from = datetime.datetime.strptime(
                data.get('created_on_from')[0],
                '%m/%d/%Y'
            )
            records = records.filter(
                created_on__gte=created_from
            )

        if data.get('created_on_until')[0]:
            created_until = datetime.datetime.strptime(
                data.get('created_on_until')[0],
                '%m/%d/%Y'
            )
            records = records.filter(
                created_on__lt=created_until
            )

        records = records.values_list('student__id', flat=True).distinct()
        return records

    def run(self, task, data):

        student_ids = self.get_result(data)
        students = Student.objects.filter(id__in=student_ids).select_related('highschool')

        start_date = datetime.datetime.strptime(
            data.get('created_on_from')[0],
            '%m/%d/%Y'
        )

        end_date = datetime.datetime.strptime(
            data.get('created_on_until')[0],
            '%m/%d/%Y'
        )
        summaries = StudentTransaction.objects.get_bulk_1098t_summary(
            student_ids=student_ids,
            start_date=start_date,
            end_date=end_date
        )

        file_name = "student-tax-data-export_" + datetime.datetime.now().strftime('%Y_%m_%d') + ".csv"
                
        result = []
        stream = io.StringIO()
        writer = csv.writer(stream, delimiter=',')

        writer.writerow([
            'Student ID', 'Name', 'ITIN', 
            'Email', 'Address', 'City', 
            'State', 'Zip Code',
            'High School', 
            'Qualified Tuition (Box 1)', 
            'Scholarships/Grants (Box 5)',
            'Payments Received (For reference)'
        ])
    
        for student in students:
            summary = summaries.get(student.id, {
                'charges': 0.0,
                'payments': 0.0,
                'scholarships': 0.0
            })
            
            # Only include students with transactions
            if summary['charges'] > 0 or summary['scholarships'] > 0:
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
                    f"{summary['payments']:.2f}"
                ])
        
        now = datetime.datetime.now().strftime("%Y/%m")
        path = f"reports/{now}/" + str(task.id) + "/" + file_name
        media_storage = PrivateMediaStorage()

        path = media_storage.save(path, ContentFile(stream.getvalue().encode('utf-8')))
        path = media_storage.url(path)

        return path

    def run_report(self):
        ...

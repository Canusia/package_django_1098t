import json
from django import forms
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from cis.models.term import Term, AcademicYear
from student_transactions.models import StudentTransaction
from cis.models.settings import Setting

from cis.validators import numeric, validate_json

class SettingForm(forms.Form):

    school_name = forms.CharField(
        help_text='',
        label="School Name"
    )
    
    school_address = forms.CharField(
        widget=forms.Textarea,
        help_text='',
        label="School Address"
    )
    
    school_ein = forms.CharField(
        help_text='',
        label="School EIN"
    )
    
    # what transactions to include for credits
    credit_pay_types = forms.MultipleChoiceField(
        choices=StudentTransaction.PAYMENT_TYPES,
        label='Credit Pay Type(s)',
        required=True,
        widget=forms.CheckboxSelectMultiple
    )

    # subtract refunds from total credit
    subtract_refunds = forms.BooleanField(
        label='Subtract Refunds from credit',
        required=False
    )

    refund_types = forms.MultipleChoiceField(
        choices=StudentTransaction.REFUND_TYPES,
        required=False,
        label='Refund Type(s) to Include',
        widget=forms.CheckboxSelectMultiple
    )
    
    # calculate scholarships
    scholarship_types = forms.MultipleChoiceField(
        choices=StudentTransaction.SCHOLARSHIP_TYPES,
        required=True,
        label='Scholarship Type(s)',
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _to_python(self):
        """
        Return dict of form elements from $_POST
        """
        result = {}
        for key, value in self.cleaned_data.items():
            result[key] = value
        
        return result


class f1098(SettingForm):
    key = str(__name__)

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = request
        self.helper = FormHelper()
        self.helper.attrs = {'target':'_blank'}
        self.helper.form_method = 'POST'
        self.helper.form_action = reverse_lazy(
            'setting:run_record', args=[request.GET.get('report_id')])
        self.helper.add_input(Submit('submit', 'Save Setting'))

    @classmethod
    def from_db(cls):
        try:
            setting = Setting.objects.get(key=cls.key)
            return setting.value
        except Setting.DoesNotExist:
            return {}

    def install(self):
        defaults = {
            'is_active': 'No',
            'footer': 'Change me in Settings -> Misc -> SMS',
            'from_phone': '19282186718'
        }

        try:
            setting = Setting.objects.get(key=self.key)
        except Setting.DoesNotExist:
            setting = Setting()
            setting.key = self.key

        setting.value = defaults
        setting.save()

    def run_record(self):
        try:
            setting = Setting.objects.get(key=self.key)
        except Setting.DoesNotExist:
            setting = Setting()
            setting.key = self.key

        setting.value = self._to_python()
        setting.save()

        return JsonResponse({
            'message': 'Successfully saved settings',
            'status': 'success'})

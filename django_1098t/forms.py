# webapp/django_1098t/django_1098t/forms.py

from django import forms
from cis.models.student import Student
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from datetime import datetime


class PublishIndividualForm1098TForm(forms.Form):
    """
    Form to publish a 1098-T for an individual student.
    """
    student_id = forms.UUIDField(
        label='Student ID',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Student GUID (e.g., 484f56ab-0403-42de-b3ae-4c8ef493e364)'
        })
    )
    
    tax_year = forms.IntegerField(
        label='Tax Year',
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter year (e.g., 2024)',
            'min': 2000,
            'max': datetime.now().year + 1
        })
    )
    
    regenerate = forms.BooleanField(
        label='Regenerate if already exists',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_id = 'publish-individual-form'
        self.helper.add_input(Submit('submit', 'Publish Form', css_class='btn btn-primary'))
    
    def clean_student_id(self):
        """Validate that the student exists."""
        student_id = self.cleaned_data.get('student_id')
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            raise forms.ValidationError(f'Student with ID {student_id} does not exist.')
        
        return student_id
    
    def clean_tax_year(self):
        """Validate tax year is reasonable."""
        tax_year = self.cleaned_data.get('tax_year')
        current_year = datetime.now().year
        
        if tax_year < 2000:
            raise forms.ValidationError('Tax year must be 2000 or later.')
        
        if tax_year > current_year + 1:
            raise forms.ValidationError(f'Tax year cannot be more than {current_year + 1}.')
        
        return tax_year
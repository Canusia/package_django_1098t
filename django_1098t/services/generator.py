# webapp/django_1098t/django_1098t/services/generator.py

from pypdf import PdfReader, PdfWriter
from typing import Dict, Optional
import io
import traceback
from django_1098t.constants import get_filer_info  # Changed import


class Form1098TGenerator:
    """Generates filled 1098-T PDF forms."""
    
    OPTIONAL_FIELD_MAPPING = {
        'filer_address': 'topmostSubform[0].CopyB[0].LeftCol[0].f2_7[0]',
        'box4_adjustments': 'topmostSubform[0].CopyB[0].RightCol[0].Box4_ReadOrder[0].f2_9[0]',
        'box6_scholarship_adjustments': 'topmostSubform[0].CopyB[0].RightCol[0].Box6_ReadOrder[0].f2_11[0]',
        'box10_insurance_refund': 'topmostSubform[0].CopyB[0].RightCol[0].f2_12[0]',
        'box7_jan_march_check': 'topmostSubform[0].CopyB[0].RightCol[0].c2_3[0]',
        'box8_halftime_check': 'topmostSubform[0].CopyB[0].RightCol[0].c2_4[0]',
        'box9_graduate_check': 'topmostSubform[0].CopyB[0].RightCol[0].c2_5[0]',
        'corrected_check': 'topmostSubform[0].CopyB[0].c2_1[0]',
    }
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        # Get filer info once during initialization
        self.filer_info = get_filer_info()
    
    def generate_filled_form(
        self,
        student_data: Dict[str, str],
        amounts: Dict[str, float],
        optional_amounts: Optional[Dict[str, float]] = None,
        checkboxes: Optional[Dict[str, bool]] = None
    ) -> io.BytesIO:
        """Generate a filled 1098-T PDF form and return as BytesIO object."""
        try:
            reader = PdfReader(self.template_path)
            writer = PdfWriter()
            writer.append(reader)
            
            # Build field data
            field_data = self._build_required_fields(student_data, amounts)
            
            # Add optional fields
            if student_data.get('address2'):
                field_data['student_address2'] = student_data['address2']
            
            # Use filer info from database
            # field_data[self.OPTIONAL_FIELD_MAPPING['filer_address']] = self.filer_info['address']
            
            if optional_amounts:
                self._add_optional_amounts(field_data, optional_amounts)
            
            if checkboxes:
                self._add_checkboxes(field_data, checkboxes)
            
            # Fill the form
            writer.update_page_form_field_values(
                writer.pages[0],
                field_data,
                auto_regenerate=False
            )
            
            # Write to BytesIO
            pdf_bytes = io.BytesIO()
            writer.write(pdf_bytes)
            pdf_bytes.seek(0)
            
            return pdf_bytes
            
        except Exception as e:
            print(f"Error filling PDF: {e}")
            traceback.print_exc()
            raise
    
    def _build_required_fields(
        self,
        student_data: Dict[str, str],
        amounts: Dict[str, float]
    ) -> Dict[str, str]:
        # Use filer info from database
        return {
            # 'filer_name': self.filer_info['name'] + '\r\n' + self.filer_info['address'],
            'filer_name': self.filer_info['name'] + '\n' + self.filer_info['address'],
            'filer_ein': self.filer_info['ein'],
            'student_name': student_data.get('name', ''),
            'student_tin': student_data.get('tin', ''),
            'student_address': student_data.get('address', ''),
            'box1_payments': self._format_currency(amounts.get('payments', 0.0)),
            'box5_scholarships': self._format_currency(amounts.get('scholarships', 0.0)),
        }
    
    def _add_optional_amounts(self, field_data: Dict, optional_amounts: Dict):
        if 'adjustments' in optional_amounts:
            field_data[self.OPTIONAL_FIELD_MAPPING['box4_adjustments']] = \
                self._format_currency(optional_amounts['adjustments'])
        
        if 'scholarship_adjustments' in optional_amounts:
            field_data[self.OPTIONAL_FIELD_MAPPING['box6_scholarship_adjustments']] = \
                self._format_currency(optional_amounts['scholarship_adjustments'])
        
        if 'insurance_refund' in optional_amounts:
            field_data[self.OPTIONAL_FIELD_MAPPING['box10_insurance_refund']] = \
                self._format_currency(optional_amounts['insurance_refund'])
    
    def _add_checkboxes(self, field_data: Dict, checkboxes: Dict):
        checkbox_mapping = {
            'jan_march': 'box7_jan_march_check',
            'halftime': 'box8_halftime_check',
            'graduate': 'box9_graduate_check',
            'corrected': 'corrected_check'
        }
        
        for key, mapping_key in checkbox_mapping.items():
            if key in checkboxes:
                field_data[self.OPTIONAL_FIELD_MAPPING[mapping_key]] = \
                    'Yes' if checkboxes[key] else 'Off'
    
    @staticmethod
    def _format_currency(amount: float) -> str:
        return f"{amount:.2f}"
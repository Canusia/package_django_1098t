# webapp/django_1098t/django_1098t/management/commands/test_1098t_generation.py

import os
from django.core.management.base import BaseCommand
from django.conf import settings
from ...services.generator import Form1098TGenerator
from ...constants import get_template_path


class Command(BaseCommand):
    """
    python manage.py test_1098t_generation 2025 --output my_test_form.pdf
    """
    help = 'Test 1098-T PDF generation with sample data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'year',
            type=int,
            help='Tax year (e.g., 2025)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='test_1098t.pdf',
            help='Output filename (default: test_1098t.pdf)'
        )
    
    def handle(self, *args, **options):
        year = options['year']
        output_filename = options['output']
        
        # Define test data
        test_data = {
            'student_data': {
                'name': 'John Test Doe',
                'tin': '123-45-6789',
                'service_provider_account_number': 'TEST-12345',
                'address': '123 Test Street',
                'address2': 'Syracuse, NY 13210'
            },
            'amounts': {
                'payments': 15000.50,
                'scholarships': 5000.00
            },
            'optional_amounts': {
                'adjustments': 250.00,
                'scholarship_adjustments': 100.00,
                'insurance_refund': 0.00
            },
            'checkboxes': {
                'jan_march': False,
                'halftime': True,
                'graduate': False,
                'corrected': False
            }
        }
        
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(f"Testing 1098-T PDF Generation")
        self.stdout.write(f"{'='*70}")
        self.stdout.write(f"Tax Year: {year}")
        self.stdout.write(f"Output File: {output_filename}\n")
        
        try:
            # Get template path
            template_path = get_template_path(year)
            self.stdout.write(f"Template: {template_path}")
            
            # Initialize generator
            generator = Form1098TGenerator(template_path)
            
            # Display test data
            self.stdout.write("\nTest Data:")
            self.stdout.write(f"  Student: {test_data['student_data']['name']}")
            self.stdout.write(f"  TIN: {test_data['student_data']['tin']}")
            self.stdout.write(f"  Account #: {test_data['student_data']['service_provider_account_number']}")
            self.stdout.write(f"  Address: {test_data['student_data']['address']}, {test_data['student_data']['address2']}")
            self.stdout.write(f"  Payments (Box 1): ${test_data['amounts']['payments']:.2f}")
            self.stdout.write(f"  Scholarships (Box 5): ${test_data['amounts']['scholarships']:.2f}")
            self.stdout.write(f"  Adjustments (Box 4): ${test_data['optional_amounts']['adjustments']:.2f}")
            self.stdout.write(f"  Half-time Student: {test_data['checkboxes']['halftime']}")
            
            # Generate PDF
            self.stdout.write("\nGenerating PDF...")
            pdf_bytes = generator.generate_filled_form(
                student_data=test_data['student_data'],
                amounts=test_data['amounts'],
                optional_amounts=test_data['optional_amounts'],
                checkboxes=test_data['checkboxes']
            )
            
            # Save to local file
            output_path = os.path.join(settings.BASE_DIR, output_filename)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes.getvalue())
            
            file_size = len(pdf_bytes.getvalue())
            
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ PDF generated successfully!")
            )
            self.stdout.write(f"File Size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
            self.stdout.write(f"Saved to: {output_path}")
            self.stdout.write(f"\nOpen with: open {output_path}\n")
            
        except FileNotFoundError as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ Error: {str(e)}\n")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ Error generating PDF: {str(e)}\n")
            )
            import traceback
            traceback.print_exc()
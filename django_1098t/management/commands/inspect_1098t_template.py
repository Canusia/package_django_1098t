# webapp/django_1098t/django_1098t/management/commands/inspect_1098t_template.py

import os
from django.core.management.base import BaseCommand
from pypdf import PdfReader
from ...constants import get_template_path


class Command(BaseCommand):
    help = 'Inspect and list all editable field names from a 1098-T PDF template'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'year',
            type=int,
            help='Tax year (e.g., 2024) - will look for templates_pdf/f1098t/{year}.pdf'
        )
        parser.add_argument(
            '--show-types',
            action='store_true',
            help='Show field types along with names'
        )
        parser.add_argument(
            '--show-values',
            action='store_true',
            help='Show current field values (if any)'
        )
    
    def handle(self, *args, **options):
        year = options['year']
        show_types = options.get('show_types', False)
        show_values = options.get('show_values', False)
        
        try:
            # Get template path using the same function as the generator
            template_path = get_template_path(year)
            
            self.stdout.write(f"\n{'='*70}")
            self.stdout.write(f"1098-T PDF Template Field Inspector")
            self.stdout.write(f"{'='*70}")
            self.stdout.write(f"Year: {year}")
            self.stdout.write(f"Path: {template_path}")
            self.stdout.write(f"{'='*70}\n")
            
            # Read the PDF
            reader = PdfReader(template_path)
            fields = reader.get_fields()
            
            if not fields:
                self.stdout.write(
                    self.style.WARNING('No form fields found in this PDF!')
                )
                self.stdout.write(
                    'This PDF may not be a fillable form, or fields may be protected.'
                )
                return
            
            # Display fields
            self.stdout.write(
                self.style.SUCCESS(f'\nFound {len(fields)} form fields:\n')
            )
            
            # Sort fields alphabetically for easier reading
            sorted_fields = sorted(fields.items(), key=lambda x: x[0])
            
            for field_name, field in sorted_fields:
                output = f"  • {field_name}"
                
                if show_types:
                    field_type = field.get('/FT', 'Unknown')
                    # Decode field type
                    type_map = {
                        '/Tx': 'Text',
                        '/Btn': 'Button/Checkbox',
                        '/Ch': 'Choice',
                        '/Sig': 'Signature'
                    }
                    readable_type = type_map.get(str(field_type), str(field_type))
                    output += f" [{readable_type}]"
                
                if show_values:
                    field_value = field.get('/V', '')
                    if field_value:
                        output += f" = '{field_value}'"
                
                self.stdout.write(output)
            
            # Summary
            self.stdout.write(f"\n{'='*70}")
            self.stdout.write(f"Total fields: {len(fields)}")
            
            # Count by type
            if show_types:
                type_counts = {}
                for field_name, field in fields.items():
                    field_type = str(field.get('/FT', 'Unknown'))
                    type_counts[field_type] = type_counts.get(field_type, 0) + 1
                
                self.stdout.write("\nField Types:")
                for ftype, count in type_counts.items():
                    type_map = {
                        '/Tx': 'Text',
                        '/Btn': 'Button/Checkbox',
                        '/Ch': 'Choice',
                        '/Sig': 'Signature'
                    }
                    readable = type_map.get(ftype, ftype)
                    self.stdout.write(f"  {readable}: {count}")
            
            self.stdout.write(f"{'='*70}\n")
            
            # Helpful tips
            self.stdout.write(
                self.style.SUCCESS('\n💡 Next Steps:')
            )
            self.stdout.write(
                '  1. Use these field names in your Form1098TGenerator.OPTIONAL_FIELD_MAPPING'
            )
            self.stdout.write(
                '  2. Update constants.py if the required fields have changed'
            )
            self.stdout.write(
                '  3. Test with: python manage.py publish_1098t {year} --student-id <id>\n'
            )
            
        except FileNotFoundError as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error: {str(e)}\n')
            )
            self.stdout.write(
                f'Expected location: templates_pdf/f1098t/{year}.pdf'
            )
            self.stdout.write(
                '\nMake sure you have placed the PDF template in the correct directory.\n'
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error reading PDF: {str(e)}\n')
            )
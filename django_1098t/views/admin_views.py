# django_1098t/views/admin_views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django_1098t.services.publisher import Form1098TPublisher
from django_1098t.models import Form1098T
from cis.models.student import Student
import csv
from datetime import datetime
import zipfile
from io import BytesIO
from django_1098t.services.storage import Form1098TStorage


@staff_member_required
def publish_forms_view(request):
    """Admin view to publish 1098-T forms."""
    if request.method == 'POST':
        tax_year = int(request.POST.get('tax_year'))
        action = request.POST.get('action')
        
        publisher = Form1098TPublisher(tax_year, request.user)
        
        if action == 'publish_all':
            results = publisher.publish_all_students()
            messages.success(
                request,
                f"Published {results['success_count']} forms. "
                f"Skipped {results['skipped_count']}. "
                f"Errors: {results['error_count']}"
            )
            if results['errors']:
                for error in results['errors'][:5]:
                    messages.error(request, f"{error['student_name']}: {error['error']}")
        
        elif action == 'publish_student':
            student_id = request.POST.get('student_id')
            student = Student.objects.get(id=student_id)
            result = publisher.publish_student_form(student, regenerate=True)
            
            if result == 'published':
                messages.success(request, f"Published form for {student.user.get_full_name()}")
            elif result == 'skipped':
                messages.warning(request, f"No qualifying transactions for {student.user.get_full_name()}")
        
        return redirect('django_1098t:admin_publish')
    
    # GET request - show form
    current_year = datetime.now().year
    years = range(current_year - 5, current_year + 1)
    
    return render(request, 'django_1098t/admin_publish.html', {
        'years': years,
        'current_year': current_year
    })


@staff_member_required
def download_statistics_view(request):
    """View download statistics for all forms."""
    tax_year = request.GET.get('tax_year', datetime.now().year)
    
    forms = Form1098T.objects.filter(
        tax_year=tax_year,
        is_published=True
    ).select_related('student__user').prefetch_related('downloads')
    
    stats = []
    for form in forms:
        stats.append({
            'student_name': form.student_name,
            'student_id': form.student.id,
            'download_count': form.download_count,
            'last_downloaded': form.last_downloaded_at,
            'published_at': form.published_at
        })
    
    # Export to CSV if requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="1098t_stats_{tax_year}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Student ID', 'Student Name', 'Downloads', 'Last Downloaded', 'Published At'])
        
        for stat in stats:
            writer.writerow([
                stat['student_id'],
                stat['student_name'],
                stat['download_count'],
                stat['last_downloaded'],
                stat['published_at']
            ])
        
        return response
    
    return render(request, 'django_1098t/admin_statistics.html', {
        'stats': stats,
        'tax_year': tax_year
    })


@staff_member_required
def bulk_download_forms(request, tax_year):
    """Download all forms for a tax year as a zip file."""
    forms = Form1098T.objects.filter(
        tax_year=tax_year,
        is_published=True
    ).select_related('student__user')
    
    storage = Form1098TStorage()
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for form in forms:
            try:
                file_content = storage.get_file_content(form.file_path)
                filename = f"{form.student.id}_{form.student_name.replace(' ', '_')}_1098T_{tax_year}.pdf"
                zf.writestr(filename, file_content)
            except Exception as e:
                print(f"Error adding {form.id}: {e}")
    
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="1098T_Forms_{tax_year}.zip"'
    
    return response
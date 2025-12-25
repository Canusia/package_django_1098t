# django_1098t/views/student_views.py

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from ..models import Form1098T, Form1098TDownload
from ..services.storage import Form1098TStorage
from cis.utils import user_has_cis_role, user_has_student_role

@login_required
def download_form(request, form_id):
    """
    Download a 1098-T form (proxied through Django for access control).
    """
    # Get the form
    form = get_object_or_404(Form1098T, id=form_id, is_published=True)
    
    if request and user_has_student_role(request.user):
        # Security: Ensure student can only download their own forms
        if not hasattr(request.user, 'student') or form.student != request.user.student:
            raise Http404("Form not found")
    elif request and not user_has_cis_role(request.user):
        raise Http404("Form not found")
    
    # Retrieve file from S3
    storage = Form1098TStorage()
    try:
        file_content = storage.get_file_content(form.file_path)
    except Exception as e:
        raise Http404("Form file not found")
    
    # Track download
    Form1098TDownload.objects.create(
        form=form,
        student=form.student,
        file_path_snapshot=form.file_path,
        ip_address=_get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
    )
    
    # Return PDF
    response = HttpResponse(file_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="1098-T_{form.tax_year}_{form.student_name.replace(" ", "_")}.pdf"'
    response['Content-Length'] = len(file_content)
    
    return response


def _get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def student_forms_list(request):
    """
    List all available 1098-T forms for the logged-in student.
    """
    if not hasattr(request.user, 'student'):
        raise Http404("Not a student account")
    
    from django.template import Context, Template
    from cis.settings.student_portal import student_portal as portal_lang
    from cis.menu import draw_menu, STUDENT_MENU

    student = request.user.student
    template = Template(portal_lang(request).from_db().get('tax_docs_blurb', 'Change me'))

    context = Context({
        'has_banner_id': student.has_banner_id(),
        'netid': student.user.secondary_email,
        'emplid': student.user.psid
    })
    intro = template.render(context)

    forms = Form1098T.objects.filter(
        student=request.user.student,
        is_published=True
    ).order_by('-tax_year')
    
    # Add download stats to each form
    forms_with_stats = []
    for form in forms:
        forms_with_stats.append({
            'form': form,
            'download_url': form.get_download_url()
        })
    
    return render(request, 'django_1098t/student_forms_list.html', {
        'intro': intro,
        'menu': draw_menu(STUDENT_MENU, 'f1098t', '', 'student'),
        'forms': forms_with_stats
    })
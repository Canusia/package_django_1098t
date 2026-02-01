# django_1098t/views/student_views.py

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
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

        # Check if student has consented to electronic delivery
        student = request.user.student
        if not student.meta or not student.meta.get('form_1098_consent_granted_on'):
            return redirect('django_1098t:student_forms_list')

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
    from ..settings.f1098 import f1098

    student = request.user.student
    menu = draw_menu(STUDENT_MENU, 'f1098t', '', 'student')

    # Check if student has consented to electronic delivery
    needs_consent = not student.meta or not student.meta.get('form_1098_consent_granted_on')

    if needs_consent:
        # Get consent language from settings
        settings_data = f1098.from_db()
        consent_language = settings_data.get('consent_language', '')

        return render(request, 'django_1098t/student_forms_list.html', {
            'menu': menu,
            'needs_consent': True,
            'consent_language': consent_language
        })

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
        'menu': menu,
        'needs_consent': False,
        'forms': forms_with_stats
    })


@login_required
@require_POST
def submit_consent(request):
    """
    Handle student consent submission for electronic 1098-T forms.
    """
    if not hasattr(request.user, 'student'):
        raise Http404("Not a student account")

    student = request.user.student

    # Store consent timestamp in student meta
    if student.meta is None:
        student.meta = {}
    student.meta['form_1098_consent_granted_on'] = timezone.now().isoformat()
    student.save()

    return redirect('django_1098t:student_forms_list')


@login_required
@require_POST
def revoke_consent(request):
    """
    Handle student revoking consent for electronic 1098-T forms.
    """
    if not hasattr(request.user, 'student'):
        raise Http404("Not a student account")

    student = request.user.student

    # Remove consent from student meta
    if student.meta and 'form_1098_consent_granted_on' in student.meta:
        del student.meta['form_1098_consent_granted_on']
        student.save()

    return redirect('django_1098t:student_forms_list')
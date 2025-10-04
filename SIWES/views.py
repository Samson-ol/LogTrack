# Ensure login_required is imported at the top
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from .forms_edit import SubmissionEditForm

@login_required
def supervisor_logs(request):
    user = request.user
    if not hasattr(user, 'user_type') or user.user_type != 'supervisor':
        from django.contrib import messages
        messages.error(request, 'You do not have permission to access this page.')
        from django.shortcuts import redirect
        return redirect('landing')
    students = CustomUser.objects.filter(user_type='student', supervisor=user)
    submissions = Submission.objects.filter(student__in=students)
    selected_student = request.GET.get('student')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status')
    from datetime import datetime, timedelta
    if selected_student:
        submissions = submissions.filter(matric_number=selected_student)
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            submissions = submissions.filter(date__gte=start)
        except Exception:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            submissions = submissions.filter(date__lt=end)
        except Exception:
            pass
    if status_filter == 'approved':
        submissions = submissions.filter(approved=True)
    elif status_filter == 'pending':
        submissions = submissions.filter(approved=False)
    submissions = submissions.order_by('-date')
    # PDF export
    if request.GET.get('export') == 'pdf':
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from xhtml2pdf import pisa
        from io import BytesIO
        
        # Build absolute file URLs for each submission
        submissions_with_urls = []
        for s in submissions:
            file_url = request.build_absolute_uri(s.file.url) if s.file else None
            submissions_with_urls.append({
                'matric_number': s.matric_number,
                'student': s.student,
                'date': s.date,
                'overview': s.overview,
                'text': s.text,
                'file_url': file_url,
                'approved': s.approved,
                'remark': s.remark,
            })
        
        # Render template to string
        html_string = render_to_string('SIWES/supervisor_logs_pdf.html', {
            'user': user,
            'students': students,
            'submissions': submissions_with_urls,
            'start_date': start_date,
            'end_date': end_date,
        })
        
        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="student_logs.pdf"'
        
        # Generate PDF
        pisa_status = pisa.CreatePDF(html_string, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors with PDF generation')
        return response
    return render(request, 'SIWES/supervisor_logs.html', {
        'user': user,
        'students': students,
        'submissions': submissions,
        'start_date': start_date,
        'end_date': end_date,
    })
from .models import Submission , CustomUser
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.views import PasswordResetView
from .custom_password_reset_form import CustomPasswordResetForm
from django.shortcuts import get_object_or_404


# Student can delete their own unapproved submission
@login_required
@require_POST
def delete_submission(request, submission_id):
    user = request.user
    submission = get_object_or_404(Submission, id=submission_id, student=user)
    if submission.approved:
        messages.error(request, 'You cannot delete an approved submission.')
    else:
        submission.delete()
        messages.success(request, 'Submission deleted successfully!')
    return redirect('student_dashboard')

# AJAX endpoint for inline supervisor remark editing
@login_required
def ajax_edit_remark(request, submission_id):
    if request.method == 'POST' and request.user.user_type == 'supervisor':
        submission = get_object_or_404(Submission, id=submission_id)
        remark = request.POST.get('remark', '').strip()
        submission.remark = remark
        submission.save()
        return JsonResponse({'success': True, 'remark': submission.remark})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# Student can edit their submission if not approved
@login_required
def edit_submission(request, submission_id):
    user = request.user
    submission = get_object_or_404(Submission, id=submission_id, student=user)
    if submission.approved:
        messages.error(request, 'You cannot edit an approved submission.')
        return redirect('student_dashboard')
    if request.method == 'POST':
        form = SubmissionEditForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, 'Submission updated successfully!')
            return redirect('student_dashboard')
    else:
        form = SubmissionEditForm(instance=submission)
    return render(request, 'SIWES/edit_submission.html', {'form': form, 'submission': submission})

class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset_form.html'

def landing(request):
    return render(request, 'SIWES/landing.html')

def login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                auth_login(request, user)
                if user.user_type == 'student':
                    return redirect('student_dashboard')
                elif user.user_type == 'supervisor':
                    return redirect('supervisor_dashboard')
                else:
                    return redirect('landing')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Invalid login details.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'SIWES/login.html', {'form': form})

# Student dashboard view
@login_required
def student_dashboard(request):
    user = request.user
    # Only allow students
    if not hasattr(user, 'user_type') or user.user_type != 'student':
        messages.error(request, 'You do not have permission to access the student dashboard.')
        return redirect('landing')
    if request.method == 'POST':
        overview = request.POST.get('overview', '').strip()
        text = request.POST.get('text')
        file = request.FILES.get('file')
        if text:
            Submission.objects.create(
                student=user,
                matric_number=user.matric_number,
                overview=overview,
                text=text,
                file=file
            )
            messages.success(request, 'Submission successful!')
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Please enter your daily log.')
    # Date filter
    from datetime import datetime, timedelta
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    submissions = Submission.objects.filter(student=user)
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            submissions = submissions.filter(date__gte=start)
        except Exception:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            submissions = submissions.filter(date__lt=end)
        except Exception:
            pass
    submissions = submissions.order_by('-date')
    # PDF export for student
    if request.GET.get('export') == 'pdf':
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from xhtml2pdf import pisa
        
        # Build submissions data with file URLs
        submissions_with_urls = []
        for s in submissions:
            file_url = request.build_absolute_uri(s.file.url) if s.file else None
            submissions_with_urls.append({
                'date': s.date,
                'overview': s.overview,
                'text': s.text,
                'file_url': file_url,
                'approved': s.approved,
                'remark': s.remark,
            })
        
        supervisor = user.supervisor if hasattr(user, 'supervisor') else None
        
        # Render template to string
        html_string = render_to_string('SIWES/student_logs_pdf.html', {
            'submissions': submissions_with_urls, 
            'user': user, 
            'supervisor': supervisor
        })
        
        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="my_logs.pdf"'
        
        # Generate PDF
        pisa_status = pisa.CreatePDF(html_string, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors with PDF generation')
        return response
    supervisor = user.supervisor if hasattr(user, 'supervisor') else None
    return render(request, 'SIWES/student_dashboard.html', {
        'user': user,
        'submissions': submissions,
        'supervisor': supervisor,
        'start_date': start_date,
        'end_date': end_date,
    })

# Supervisor dashboard view
@login_required
def supervisor_dashboard(request):
    import csv
    # from django.http import HttpResponse
    user = request.user
    # Only allow supervisors
    if not hasattr(user, 'user_type') or user.user_type != 'supervisor':
        messages.error(request, 'You do not have permission to access the supervisor dashboard.')
        return redirect('landing')
    # Approve a submission if requested
    if request.method == 'POST' and 'approve_id' in request.POST:
        approve_id = request.POST.get('approve_id')
        remark = request.POST.get('remark', '').strip()
        try:
            submission = Submission.objects.get(id=approve_id)
            submission.approved = True
            submission.reviewed_by = user
            if remark:
                submission.remark = remark
            submission.save()
            messages.success(request, f'Submission {submission.id} approved!')
        except Submission.DoesNotExist:
            messages.error(request, 'Submission not found.')
        return redirect('supervisor_dashboard')

    students = []
    submissions = []
    filter_date = request.GET.get('filter_date')
    status_filter = request.GET.get('status')
    selected_student = request.GET.get('student')
    if user.user_type == 'supervisor':
        students = CustomUser.objects.filter(user_type='student', supervisor=user)
        submissions = Submission.objects.filter(student__in=students)
        if selected_student:
            submissions = submissions.filter(matric_number=selected_student)
        if filter_date:
            from datetime import datetime, timedelta
            start = datetime.strptime(filter_date, '%Y-%m-%d')
            end = start + timedelta(days=1)
            submissions = submissions.filter(date__gte=start, date__lt=end)
        if status_filter == 'approved':
            submissions = submissions.filter(approved=True)
        elif status_filter == 'pending':
            submissions = submissions.filter(approved=False)
        submissions = submissions.order_by('-date')

    # CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="submissions.csv"'
        writer = csv.writer(response)
        writer.writerow(['Matric Number', 'Student Name', 'Date', 'Text', 'File', 'Approved', 'Remark'])
        for s in submissions:
            writer.writerow([
                s.matric_number,
                s.student.get_full_name() if s.student.get_full_name() else s.student.email,
                s.date,
                s.text,
                s.file.url if s.file else '',
                'Yes' if s.approved else 'No',
                s.remark or ''
            ])
        return response

    return render(request, 'SIWES/supervisor_dashboard.html', {
        'user': user,
        'students': students,
        'submissions': submissions,
        'filter_date': filter_date,
        'status_filter': status_filter,
        'selected_student': selected_student,
    })

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'SIWES/register.html', {'form': form})

def rules(request):
    return render(request, 'SIWES/rules.html')
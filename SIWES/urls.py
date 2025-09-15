from django.urls import path
from django.views.generic import RedirectView
from . import views
from django.contrib.auth import views as auth_views

# Create your urls here
urlpatterns = [
    path('', views.landing, name = 'landing'),
    path('login/', views.login, name = 'login'),
    path('register/', views.register, name = 'register'),
    path('rules/', views.rules, name = 'rules'),
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('accounts/login/', RedirectView.as_view(pattern_name='login', permanent=False)),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/submission/<int:submission_id>/edit/', views.edit_submission, name='edit_submission'),
    path('student/delete_submission/<int:submission_id>/', views.delete_submission, name='delete_submission'),
    path('supervisor/dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/ajax/edit_remark/<int:submission_id>/', views.ajax_edit_remark, name='ajax_edit_remark'),
    path('supervisor/logs/', views.supervisor_logs, name='supervisor_logs'),
]
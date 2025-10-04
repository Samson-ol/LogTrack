from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Submission
from django.contrib import messages
from django.db import models
from django import forms
from .forms_admin import CustomUserForm  # Import the form from forms_admin.py

# @admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'user_type', 'department', 'matric_number', 'lecturer_id', 'supervisor', 'is_staff', 'is_active')
    list_filter = ('user_type', 'department', 'is_staff', 'is_active')
    search_fields = ('email', 'matric_number', 'lecturer_id', 'first_name', 'last_name', 'department')
    ordering = ('email',)
    actions = ['map_students_to_supervisors']
    
    base_fieldsets = (
        (None, {'fields': ('email', 'password', 'user_type', 'title', 'department', 'matric_number', 'lecturer_id')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        # Add students field for supervisors
        if obj and getattr(obj, 'user_type', None) == 'supervisor':
            fields.append('students')
        return fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(self.base_fieldsets)
        # Only add 'supervisor' for students if obj exists and is a student
        if obj is not None and getattr(obj, 'user_type', None) == 'student':
            fieldsets[0][1]['fields'] = fieldsets[0][1]['fields'] + ('supervisor',)
        return fieldsets

    form = CustomUserForm
    readonly_fields = UserAdmin.readonly_fields + ('students_list',)
    
    def students_list(self, obj):
        if obj.user_type == 'supervisor':
            # List of students assigned to this supervisor
            return ', '.join([s.email for s in obj.students.all()])
        return ''
    students_list.short_description = 'Assigned Students'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        from django import forms as djforms
        
        # Always remove supervisor and students fields first to avoid conflicts
        if 'supervisor' in form.base_fields:
            form.base_fields.pop('supervisor')
        if 'students' in form.base_fields:
            form.base_fields.pop('students')
        
        # Show 'Assign Students' only for supervisors
        if obj and getattr(obj, 'user_type', None) == 'supervisor':
            students_qs = CustomUser.objects.filter(user_type='student')
            form.base_fields['students'] = djforms.ModelMultipleChoiceField(
                queryset=students_qs,
                required=False,
                widget=djforms.SelectMultiple,
                label='Assign Students'
            )
            form.base_fields['students'].initial = obj.students.all()
            
        # Add supervisor field only for students
        elif obj and getattr(obj, 'user_type', None) == 'student':
            supervisor_qs = CustomUser.objects.filter(user_type='supervisor')
            form.base_fields['supervisor'] = djforms.ModelChoiceField(
                queryset=supervisor_qs,
                required=False,
                widget=djforms.Select,
                label='Supervisor'
            )
            if obj.supervisor:
                form.base_fields['supervisor'].initial = obj.supervisor
                
        return form

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_type', 'title', 'department', 'matric_number', 'lecturer_id', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )

    def save_model(self, request, obj, form, change):
        # Auto-generate a unique username if not provided
        if not obj.username:
            base_username = obj.email.split('@')[0]
            unique_username = base_username
            counter = 1
            while CustomUser.objects.filter(username=unique_username).exists():
                unique_username = f"{base_username}{counter}"
                counter += 1
            obj.username = unique_username
        
        super().save_model(request, obj, form, change)
        
        # Save supervisor for students only if the field exists in cleaned_data
        if (obj.user_type == 'student' and 
            hasattr(form, 'cleaned_data') and 
            'supervisor' in form.cleaned_data and 
            form.cleaned_data['supervisor'] is not None):
            obj.supervisor = form.cleaned_data['supervisor']
            obj.save()
            
        # Save assigned students for supervisors only if the field exists in cleaned_data
        if (obj.user_type == 'supervisor' and 
            hasattr(form, 'cleaned_data') and 
            'students' in form.cleaned_data):
            students = form.cleaned_data['students']
            # Set supervisor for selected students
            for student in students:
                student.supervisor = obj
                student.save()
            # Unassign students not selected
            CustomUser.objects.filter(user_type='student', supervisor=obj).exclude(id__in=[s.id for s in students]).update(supervisor=None)
    
    def map_students_to_supervisors(self, request, queryset):
        """Map students to supervisors based on lecturer_id"""
        total_mapped = 0
        for supervisor in queryset.filter(user_type='supervisor'):
            if not supervisor.lecturer_id:
                continue
                
            # Find students whose matric number starts with lecturer_id
            students = CustomUser.objects.filter(
                user_type='student', 
                matric_number__startswith=supervisor.lecturer_id,
                supervisor__isnull=True  # Only unassigned students
            )
            
            # Assign supervisor to these students
            count = students.count()
            if count > 0:
                students.update(supervisor=supervisor)
                total_mapped += count
                
                self.message_user(
                    request, 
                    f"Assigned {count} students to {supervisor.get_full_name() or supervisor.username}",
                    messages.SUCCESS
                )
        
        if total_mapped == 0:
            self.message_user(
                request,
                "No new student assignments were made. Check lecturer IDs and student matric numbers.",
                messages.WARNING
            )
        else:
            self.message_user(
                request,
                f"Successfully mapped {total_mapped} students to supervisors based on lecturer ID.",
                messages.SUCCESS
            )
    
    map_students_to_supervisors.short_description = "Map selected supervisors to students by lecturer ID"

# Remove this line since you're using the @admin.register decorator above
admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'matric_number', 'date', 'approved', 'reviewed_by')
    list_filter = ('approved', 'date')
    search_fields = ('student__email', 'matric_number', 'reviewed_by__email')
    date_hierarchy = 'date'
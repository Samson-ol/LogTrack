from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Submission
from .forms_admin import CustomUserForm


class CustomUserAdmin(UserAdmin):
	model = CustomUser
	list_display = ('email', 'user_type', 'matric_number', 'supervisor', 'is_staff', 'is_active')
	list_filter = ('user_type', 'is_staff', 'is_active')
	search_fields = ('email', 'matric_number', 'first_name', 'last_name')
	ordering = ('email',)
	base_fieldsets = (
		(None, {'fields': ('email', 'password', 'user_type', 'title', 'matric_number')}),
		('Personal info', {'fields': ('first_name', 'last_name')}),
		('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		('Important dates', {'fields': ('last_login', 'date_joined')}),
	)

	def get_fieldsets(self, request, obj=None):
		fieldsets = list(self.base_fieldsets)
		# Only add 'supervisor' for students if obj exists and is a student
		if obj is not None and getattr(obj, 'user_type', None) == 'student':
			fieldsets[0][1]['fields'] = fieldsets[0][1]['fields'] + ('supervisor',)
		return fieldsets

	form = CustomUserForm

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		# Save supervisor for students
		if obj.user_type == 'student' and 'supervisor' in form.cleaned_data:
			obj.supervisor = form.cleaned_data['supervisor']
			obj.save()
		# Save assigned students for supervisors
		if obj.user_type == 'supervisor' and 'students' in form.cleaned_data:
			students = form.cleaned_data['students']
			for student in students:
				student.supervisor = obj
				student.save()
			# Unassign students not selected
			CustomUser.objects.filter(user_type='student', supervisor=obj).exclude(id__in=[s.id for s in students]).update(supervisor=None)
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
		if obj and obj.user_type == 'supervisor':
			# Add students field, remove supervisor field
			students_qs = CustomUser.objects.filter(user_type='student')
			form.base_fields['students'] = djforms.ModelMultipleChoiceField(
				queryset=students_qs,
				required=False,
				widget=djforms.SelectMultiple,
				label='Assign Students'
			)
			form.base_fields['students'].initial = obj.students.all()
			if 'supervisor' in form.base_fields:
				form.base_fields.pop('supervisor')
		else:
			# Remove students field for non-supervisors
			if 'students' in form.base_fields:
				form.base_fields.pop('students')
		return form

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		# Save assigned students if supervisor
		if obj.user_type == 'supervisor' and 'students' in form.cleaned_data:
			students = form.cleaned_data['students']
			# Set supervisor for selected students
			for student in students:
				student.supervisor = obj
				student.save()
			# Unassign students not selected
			CustomUser.objects.filter(user_type='student', supervisor=obj).exclude(id__in=[s.id for s in students]).update(supervisor=None)
	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('email', 'user_type', 'title', 'matric_number', 'supervisor', 'password1', 'password2', 'is_staff', 'is_active')
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

admin.site.register(CustomUser, CustomUserAdmin)

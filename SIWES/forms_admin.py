from django import forms
from .models import CustomUser

class CustomUserForm(forms.ModelForm):
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save supervisor for students only if field exists in cleaned_data
        if hasattr(self, 'cleaned_data') and 'supervisor' in self.cleaned_data and self.cleaned_data['supervisor']:
            instance.supervisor = self.cleaned_data['supervisor']
        if commit:
            instance.save()
            # Save students for supervisors only if field exists in cleaned_data
            if hasattr(self, 'cleaned_data') and 'students' in self.cleaned_data:
                students = self.cleaned_data['students']
                # Set supervisor for selected students
                for student in students:
                    student.supervisor = instance
                    student.save()
                # Unassign students not selected
                CustomUser.objects.filter(user_type='student', supervisor=instance).exclude(id__in=[s.id for s in students]).update(supervisor=None)
        return instance
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'user_type', 'title', 'department', 'matric_number',
            'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions', 'last_login', 'date_joined', 'lecturer_id',
        ]
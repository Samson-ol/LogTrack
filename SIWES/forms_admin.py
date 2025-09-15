from django import forms
from .models import CustomUser

class CustomUserForm(forms.ModelForm):
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save supervisor for students
        if hasattr(self, 'cleaned_data') and 'supervisor' in self.cleaned_data:
            instance.supervisor = self.cleaned_data['supervisor']
        if commit:
            instance.save()
            # Save students for supervisors
            if hasattr(self, 'cleaned_data') and 'students' in self.cleaned_data:
                instance.students.set(self.cleaned_data['students'])
        return instance
    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'user_type', 'title', 'matric_number',
            'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions', 'last_login', 'date_joined'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance and instance.user_type == 'student':
            self.fields['supervisor'] = forms.ModelChoiceField(
                queryset=CustomUser.objects.filter(user_type='supervisor'),
                required=False,
                label='Supervisor'
            )
            self.fields['supervisor'].initial = instance.supervisor
        elif instance and instance.user_type == 'supervisor':
            self.fields['students'] = forms.ModelMultipleChoiceField(
                queryset=CustomUser.objects.filter(user_type='student'),
                required=False,
                widget=forms.SelectMultiple,
                label='Assign Students'
            )
            self.fields['students'].initial = instance.students.all()

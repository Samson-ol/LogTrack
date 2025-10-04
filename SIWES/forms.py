from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    title = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Title (e.g., Dr, Prof, Mr, Mrs)',
            'id': 'title',
        })
    )
    fullname = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your fullname...',
            'id': 'fullname',
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email...',
            'id': 'email',
        })
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your department...',
            'id': 'department',
        })
    )
    user_type = forms.ChoiceField(
        choices=[('select_role', 'Select role...')] + list(CustomUser.USER_TYPE_CHOICES),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_user_type',
        })
    )

    # Add this field to your CustomUserCreationForm class after the matric_number field

    lecturer_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter lecturer ID...',
            'id': 'lecturer_id',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the first option as selected and disabled (acts as a placeholder)
        self.fields['user_type'].choices = [('select_role', 'Select role...')] + list(CustomUser.USER_TYPE_CHOICES)
        self.fields['user_type'].widget.attrs['required'] = True
    matric_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter matric number...',
            'id': 'matric_number',
        })
    )
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password...',
            'id': 'password1',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password...',
            'id': 'password2',
        })
    )

    class Meta:
        model = CustomUser
        fields = ('fullname', 'email', 'department', 'user_type', 'title', 'matric_number','lecturer_id', 'password1', 'password2')

    def save(self, commit=True):
        import uuid
        user = super().save(commit=False)
        fullname = self.cleaned_data.get('fullname')
        if fullname:
            names = fullname.split()
            user.first_name = names[0]
            user.last_name = ' '.join(names[1:]) if len(names) > 1 else ''
        user.user_type = self.cleaned_data.get('user_type')
        user.email = self.cleaned_data.get('email')
        user.department = self.cleaned_data.get('department', '')
        # Generate a unique username if not set
        if not user.username:
            base_username = user.email.split('@')[0]
            unique_username = base_username
            counter = 1
            from .models import CustomUser
            while CustomUser.objects.filter(username=unique_username).exists():
                unique_username = f"{base_username}{counter}"
                counter += 1
            user.username = unique_username
        if user.user_type == 'student':
            user.matric_number = self.cleaned_data.get('matric_number')
            user.title = ''
            user.lecturer_id = None
        else:
            user.matric_number = None
            user.title = self.cleaned_data.get('title', '')
            user.lecturer_id = self.cleaned_data.get('lecturer_id', '')
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email...',
            'id': 'email',
        })
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password...',
            'id': 'password1',
        })
    )

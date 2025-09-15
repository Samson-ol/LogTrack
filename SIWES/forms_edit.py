from django import forms
from .models import Submission

class SubmissionEditForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['overview', 'text', 'file']
        widgets = {
            'overview': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short summary of your day...'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe in detail what you did today...'}),
        }

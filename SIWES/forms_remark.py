from django import forms
from .models import Submission

class SupervisorRemarkForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['remark']
        widgets = {
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Edit remark...'}),
        }

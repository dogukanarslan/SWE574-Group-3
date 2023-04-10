# forms.py
from django import forms
from .models import textAnnotation

class AnnotationForm(forms.ModelForm):
    class Meta:
        model = textAnnotation
        fields = ['type', 'body_description', 'selector_type', 'start', 'end']
        widgets = {
            'type': forms.TextInput(attrs={'class': 'form-control'}),
            'body_description': forms.Textarea(attrs={'class': 'form-control'}),
            'selector_type': forms.Select(attrs={'class': 'form-control'}),
            'start': forms.NumberInput(attrs={'class': 'form-control'}),
            'end': forms.NumberInput(attrs={'class': 'form-control'}),
        }

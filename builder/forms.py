from django import forms

from .models import Build


class BuildForm(forms.ModelForm):
    class Meta:
        model = Build
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                                 'placeholder': 'Для чого ця збірка?'}),
        }

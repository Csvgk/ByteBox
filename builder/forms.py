from django import forms

from .models import Build


class BuildForm(forms.ModelForm):
    """Редагування назви і опису власної збірки (деталі змінюються в конфігураторі)."""

    class Meta:
        model = Build
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                                 'placeholder': 'Для чого ця збірка?'}),
        }

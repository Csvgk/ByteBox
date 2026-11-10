from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Ім'я", max_length=150)
    email = forms.EmailField(label='Email')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Користувач з таким email вже зареєстрований.')
        return email

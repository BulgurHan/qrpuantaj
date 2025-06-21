from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
import datetime





class SignInForm(forms.Form):

    email = forms.CharField(
        required=True,
        widget = forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'E-Mail:'
        })
    )
    password = forms.CharField(
    required=True,
    widget = forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Parola:'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'password')
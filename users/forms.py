from django import forms
from .models import User

class StaffForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(),   # ← Parantez eklendi
        required=False,
        help_text="Yeni şifre vermek istemiyorsan boş bırak."
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user



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
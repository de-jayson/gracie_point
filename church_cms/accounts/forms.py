"""
Accounts Forms
Login and user management forms
"""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class LoginForm(forms.Form):
    """Login with username and password."""

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500',
            'placeholder': 'Username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500',
            'placeholder': 'Password',
        })
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self._user  = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username     = cleaned_data.get('username', '').strip()
        password     = cleaned_data.get('password', '')

        if username and password:
            user = authenticate(request=self.request, username=username, password=password)
            if user is None:
                raise forms.ValidationError('Invalid username or password.')
            if not user.is_active:
                raise forms.ValidationError('This account has been disabled.')
            self._user = user

        return cleaned_data

    def get_user(self):
        return self._user


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new staff users."""

    class Meta:
        model  = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500',
            })


class CustomUserChangeForm(UserChangeForm):
    """Form for editing existing users."""
    password = None

    class Meta:
        model  = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500',
            })

from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Church


class ChurchRegistrationForm(forms.Form):
    # ── Church Information ────────────────────────────────────────────────────
    church_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Grace Point Chapel'}),
    )
    church_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'church@example.org'}),
    )
    church_phone = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'placeholder': '+1 (555) 000-0000'}),
    )
    church_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Church address'}),
    )

    # ── Administrator Information ─────────────────────────────────────────────
    admin_full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Pastor Daniel'}),
    )
    admin_username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. pastor.daniel'}),
        help_text='This is what you will use to log in.',
    )
    admin_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'pastor@example.org'}),
    )
    admin_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        validators=[validate_password],
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
    )

    def clean_church_email(self):
        email = self.cleaned_data['church_email']
        if Church.objects.filter(email=email).exists():
            raise forms.ValidationError('A church with this email is already registered.')
        return email

    def clean_admin_username(self):
        from django.contrib.auth import get_user_model
        User     = get_user_model()
        username = self.cleaned_data['admin_username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('That username is already taken.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('admin_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

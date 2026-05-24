"""
Members Forms
"""

from django import forms
from .models import Member

INPUT_CLASS = 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'
SELECT_CLASS = 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'


class MemberForm(forms.ModelForm):
    """Form for creating and editing church members."""

    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'gender', 'date_of_birth', 'address',
            'date_joined', 'status', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'email@example.com'}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '+233 xx xxx xxxx'}),
            'gender': forms.Select(attrs={'class': SELECT_CLASS}),
            'date_of_birth': forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3, 'placeholder': 'Full address'}),
            'date_joined': forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'notes': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3, 'placeholder': 'Additional notes...'}),
        }

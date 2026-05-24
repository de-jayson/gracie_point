"""Attendance Forms - headcount per demographic category."""

from django import forms
from .models import ServiceAttendance

INPUT_CLASS = 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'
NUM_CLASS   = 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 text-center text-lg font-semibold placeholder-zinc-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'
SELECT_CLASS = 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'


class ServiceAttendanceForm(forms.ModelForm):
    class Meta:
        model = ServiceAttendance
        fields = [
            'event_name', 'service_type', 'date',
            'adults_male', 'adults_female',
            'junior_youth_male', 'junior_youth_female',
            'children_male', 'children_female',
            'notes',
        ]
        widgets = {
            'event_name':        forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. Sunday Service – 29th April 2025'}),
            'service_type':      forms.Select(attrs={'class': SELECT_CLASS}),
            'date':              forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'adults_male':       forms.NumberInput(attrs={'class': NUM_CLASS, 'min': 0, 'placeholder': '0'}),
            'adults_female':     forms.NumberInput(attrs={'class': NUM_CLASS, 'min': 0, 'placeholder': '0'}),
            'junior_youth_male': forms.NumberInput(attrs={'class': NUM_CLASS, 'min': 0, 'placeholder': '0'}),
            'junior_youth_female': forms.NumberInput(attrs={'class': NUM_CLASS, 'min': 0, 'placeholder': '0'}),
            'children_male':     forms.NumberInput(attrs={'class': NUM_CLASS, 'min': 0, 'placeholder': '0'}),
            'children_female':   forms.NumberInput(attrs={'class': NUM_CLASS, 'min': 0, 'placeholder': '0'}),
            'notes':             forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3, 'placeholder': 'Any additional notes for this service...'}),
        }

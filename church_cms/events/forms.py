"""Events Forms"""

from django import forms
from .models import Event

INPUT_CLASS = 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'
SELECT_CLASS = 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'


class EventForm(forms.ModelForm):
    """Form for creating and editing events."""

    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'date', 'start_time', 'end_time', 'location']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Event title'}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4, 'placeholder': 'Describe the event...'}),
            'event_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'date': forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time'}),
            'location': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Venue / location'}),
        }

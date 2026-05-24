"""Events Views"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from datetime import date
from .models import Event
from .forms import EventForm


@method_decorator(login_required, name='dispatch')
class EventListView(View):
    """Lists upcoming and past events."""
    template_name = 'events/event_list.html'

    def get(self, request):
        today = date.today()
        upcoming = Event.objects.filter(date__gte=today).order_by('date')
        past = Event.objects.filter(date__lt=today).order_by('-date')[:10]
        return render(request, self.template_name, {
            'upcoming': upcoming,
            'past': past,
        })


@method_decorator(login_required, name='dispatch')
class EventDetailView(View):
    """Shows full event details."""
    template_name = 'events/event_detail.html'

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        return render(request, self.template_name, {'event': event})


@method_decorator(login_required, name='dispatch')
class EventCreateView(View):
    """Creates a new event."""
    template_name = 'events/event_form.html'

    def get(self, request):
        form = EventForm()
        return render(request, self.template_name, {'form': form, 'title': 'New Event'})

    def post(self, request):
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, f'Event "{event.title}" created successfully.')
            return redirect('events:list')
        return render(request, self.template_name, {'form': form, 'title': 'New Event'})


@method_decorator(login_required, name='dispatch')
class EventEditView(View):
    """Edits an existing event."""
    template_name = 'events/event_form.html'

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        form = EventForm(instance=event)
        return render(request, self.template_name, {'form': form, 'title': 'Edit Event', 'event': event})

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated.')
            return redirect('events:list')
        return render(request, self.template_name, {'form': form, 'title': 'Edit Event', 'event': event})


@method_decorator(login_required, name='dispatch')
class EventDeleteView(View):
    """Deletes an event."""

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        event.delete()
        messages.success(request, 'Event deleted.')
        return redirect('events:list')

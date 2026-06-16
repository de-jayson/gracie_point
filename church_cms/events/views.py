"""Events Views"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from datetime import date
from .models import Event
from .forms import EventForm
from dashboard.cache_utils import bust_events_cache


@method_decorator(login_required, name='dispatch')
class EventListView(View):
    """Lists upcoming and past events for this church."""
    template_name = 'events/event_list.html'

    def get(self, request):
        today    = date.today()
        upcoming = Event.objects.filter(church=request.user.church, date__gte=today).order_by('date')
        past     = Event.objects.filter(church=request.user.church, date__lt=today).order_by('-date')[:10]
        return render(request, self.template_name, {
            'upcoming': upcoming,
            'past':     past,
        })


@method_decorator(login_required, name='dispatch')
class EventDetailView(View):
    """Shows full event details."""
    template_name = 'events/event_detail.html'

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk, church=request.user.church)
        return render(request, self.template_name, {'event': event})


@method_decorator(login_required, name='dispatch')
class EventCreateView(View):
    """Creates a new event and assigns it to this church."""
    template_name = 'events/event_form.html'

    def get(self, request):
        form = EventForm()
        return render(request, self.template_name, {'form': form, 'title': 'New Event'})

    def post(self, request):
        form = EventForm(request.POST)
        if form.is_valid():
            event            = form.save(commit=False)
            event.church     = request.user.church
            event.created_by = request.user
            event.save()
            bust_events_cache(request.user.church)       # ← new event added
            messages.success(request, f'Event "{event.title}" created successfully.')
            return redirect('events:list')
        return render(request, self.template_name, {'form': form, 'title': 'New Event'})


@method_decorator(login_required, name='dispatch')
class EventEditView(View):
    """Edits an existing event within this church."""
    template_name = 'events/event_form.html'

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk, church=request.user.church)
        form  = EventForm(instance=event)
        return render(request, self.template_name, {'form': form, 'title': 'Edit Event', 'event': event})

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk, church=request.user.church)
        form  = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            bust_events_cache(request.user.church)       # ← event date/details may have changed
            messages.success(request, 'Event updated.')
            return redirect('events:list')
        return render(request, self.template_name, {'form': form, 'title': 'Edit Event', 'event': event})


@method_decorator(login_required, name='dispatch')
class EventDeleteView(View):
    """Deletes an event within this church."""

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk, church=request.user.church)
        event.delete()
        bust_events_cache(request.user.church)           # ← event removed
        messages.success(request, 'Event deleted.')
        return redirect('events:list')

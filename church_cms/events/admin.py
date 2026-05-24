"""Events Admin Configuration"""

from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'date', 'location', 'created_by')
    list_filter = ('event_type', 'date')
    search_fields = ('title', 'location')
    date_hierarchy = 'date'

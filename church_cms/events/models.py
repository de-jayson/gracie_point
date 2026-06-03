"""
Events Models
Church events management
"""
 
from django.db import models
from django.conf import settings
 
 
class Event(models.Model):
    """A church event."""
 
    church = models.ForeignKey(
        "organizations.Church", on_delete=models.CASCADE, related_name="events"
    )
 
    class EventType(models.TextChoices):
        CONFERENCE  = 'conference',  'Conference'
        OUTREACH    = 'outreach',    'Outreach'
        WORSHIP     = 'worship',     'Worship Night'
        ANNIVERSARY = 'anniversary', 'Anniversary'
        TRAINING    = 'training',    'Training'
        OTHER       = 'other',       'Other'
 
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    event_type  = models.CharField(max_length=20, choices=EventType.choices, default=EventType.OTHER)
    date        = models.DateField()
    start_time  = models.TimeField(blank=True, null=True)
    end_time    = models.TimeField(blank=True, null=True)
    location    = models.CharField(max_length=300, blank=True, null=True)
 
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,       # ← changed from direct CustomUser import
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['date']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
 
    def __str__(self):
        return f"{self.title} ({self.date})"
 
    @property
    def is_past(self):
        from datetime import date
        return self.date < date.today()
 
    @property
    def is_upcoming(self):
        from datetime import date
        return self.date >= date.today()
 
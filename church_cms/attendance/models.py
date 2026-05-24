"""
Attendance Models
Records headcounts per service session — NOT tied to individual members.
Broken down by demographic category (Adults M/F, Junior Youth M/F, Children M/F).
"""

from django.db import models


class ServiceAttendance(models.Model):
    """
    A single service session with attendance headcounts by category.
    No member linkage — just totals per demographic group.
    """

    class ServiceType(models.TextChoices):
        SUNDAY = 'sunday', 'Sunday Service'
        MIDWEEK = 'midweek', 'Midweek Service'
        SPECIAL = 'special', 'Special Service'
        PRAYER = 'prayer', 'Prayer Meeting'
        YOUTH = 'youth', 'Youth Service'
        OTHER = 'other', 'Other'

    # Service info
    event_name = models.CharField(
        max_length=300,
        help_text='Type the name of the service or event (e.g. "Sunday 29th April 2025")'
    )
    service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices,
        default=ServiceType.SUNDAY
    )
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)

    # Adults
    adults_male = models.PositiveIntegerField(default=0, verbose_name='Adults Male')
    adults_female = models.PositiveIntegerField(default=0, verbose_name='Adults Female')

    # Junior Youth
    junior_youth_male = models.PositiveIntegerField(default=0, verbose_name='Junior Youth Male')
    junior_youth_female = models.PositiveIntegerField(default=0, verbose_name='Junior Youth Female')

    # Children Service
    children_male = models.PositiveIntegerField(default=0, verbose_name='Children Male')
    children_female = models.PositiveIntegerField(default=0, verbose_name='Children Female')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.event_name} ({self.date})"

    @property
    def adults_total(self):
        return self.adults_male + self.adults_female

    @property
    def junior_youth_total(self):
        return self.junior_youth_male + self.junior_youth_female

    @property
    def children_total(self):
        return self.children_male + self.children_female

    @property
    def grand_total(self):
        return self.adults_total + self.junior_youth_total + self.children_total

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Service Attendance'
        verbose_name_plural = 'Service Attendances'

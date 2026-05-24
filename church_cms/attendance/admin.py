"""Attendance Admin Configuration"""
from django.contrib import admin
from .models import ServiceAttendance

@admin.register(ServiceAttendance)
class ServiceAttendanceAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'service_type', 'date', 'adults_total', 'junior_youth_total', 'children_total', 'grand_total')
    list_filter = ('service_type', 'date')
    search_fields = ('event_name',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')

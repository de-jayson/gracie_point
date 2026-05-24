"""Members Admin Configuration"""

from django.contrib import admin
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'status', 'date_joined')
    list_filter = ('status', 'gender', 'date_joined')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    ordering = ('last_name', 'first_name')
    date_hierarchy = 'date_joined'

from django.contrib import admin
from .models import Church


@admin.register(Church)
class ChurchAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "is_active", "created_at"]
    search_fields = ["name", "email"]
    list_filter = ["is_active", "created_at"]
    ordering = ["name"]

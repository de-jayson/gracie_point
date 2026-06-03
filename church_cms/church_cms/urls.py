"""
Church Management System - Main URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # organizations first — register/ must be reachable before the root redirect
    path('', include('organizations.urls', namespace='organizations')),
    # root redirect comes after so /register/ is matched first
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),

    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('members/', include('members.urls')),
    path('attendance/', include('attendance.urls')),
    path('finance/', include('finance.urls')),
    path('events/', include('events.urls')),
]

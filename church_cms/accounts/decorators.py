"""
Accounts Decorators
Role-based access control decorators
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Restricts view to Admin users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_admin_user or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard:index')
    return wrapper


def finance_required(view_func):
    """Restricts view to Admin or Finance Officer users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_admin_user or request.user.is_finance_officer or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
        messages.error(request, 'Access denied. Finance Officer privileges required.')
        return redirect('dashboard:index')
    return wrapper


def pastor_or_admin_required(view_func):
    """Restricts view to Pastor or Admin users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_admin_user or request.user.is_pastor or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
        messages.error(request, 'Access denied. Pastor or Admin privileges required.')
        return redirect('dashboard:index')
    return wrapper

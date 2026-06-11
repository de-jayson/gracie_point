"""
dashboard/cache_utils.py

Call these functions whenever you create, update, or delete records
so the dashboard cache stays accurate.

Usage — in any view that changes data:
    from dashboard.cache_utils import bust_member_cache, bust_finance_cache

    # After adding/removing a member:
    bust_member_cache(request.user.church)

    # After recording an offering or approving an expense:
    bust_finance_cache(request.user.church)
"""

from django.core.cache import cache


def bust_member_cache(church):
    """Call after adding, editing, or removing a member."""
    cid = church.id
    cache.delete_many([
        f'dash_total_members_{cid}',
        f'dash_new_members_{cid}',
        f'dash_recent_members_{cid}',
    ])


def bust_finance_cache(church):
    """Call after recording an offering or approving/rejecting an expense."""
    cid = church.id
    cache.delete_many([
        f'dash_total_contributions_{cid}',
        f'dash_month_contributions_{cid}',
        f'dash_recent_offerings_{cid}',
    ])


def bust_attendance_cache(church):
    """Call after recording or editing attendance."""
    cache.delete(f'dash_latest_service_{church.id}')


def bust_events_cache(church):
    """Call after creating, editing, or deleting an event."""
    cache.delete(f'dash_upcoming_events_{church.id}')


def bust_all_dashboard_cache(church):
    """Nuclear option — clears everything for this church."""
    cid = church.id
    cache.delete_many([
        f'dash_total_members_{cid}',
        f'dash_new_members_{cid}',
        f'dash_recent_members_{cid}',
        f'dash_total_contributions_{cid}',
        f'dash_month_contributions_{cid}',
        f'dash_recent_offerings_{cid}',
        f'dash_latest_service_{cid}',
        f'dash_upcoming_events_{cid}',
    ])

"""Dashboard Views"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache
from django.db.models import Sum
from datetime import date, datetime
from members.models import Member
from attendance.models import ServiceAttendance
from finance.models import ServiceOffering
from events.models import Event


# ── Cache timeouts ────────────────────────────────────────────────────────────
# Adjust these numbers (in seconds) to suit how often your data changes

CACHE_5_MIN  = 60 * 5    # member counts, attendance — change occasionally
CACHE_10_MIN = 60 * 10   # finance totals — heavier queries, change less often
CACHE_1_MIN  = 60 * 1    # recent lists — users expect these to be fairly fresh


def _get_dashboard_stats(church, today, this_month_start):
    """
    Builds and caches the expensive dashboard statistics.
    Each stat has its own cache key so they expire independently
    and invalidation is surgical (e.g. only bust member cache when
    a member is added, not the whole dashboard).
    """
    cid = church.id  # shorthand for cache keys

    # ── Member counts ─────────────────────────────────────────────────────────
    total_members = cache.get(f'dash_total_members_{cid}')
    if total_members is None:
        total_members = Member.objects.filter(church=church, status='active').count()
        cache.set(f'dash_total_members_{cid}', total_members, CACHE_5_MIN)

    new_members_this_month = cache.get(f'dash_new_members_{cid}')
    if new_members_this_month is None:
        new_members_this_month = Member.objects.filter(
            church=church, date_joined__gte=this_month_start
        ).count()
        cache.set(f'dash_new_members_{cid}', new_members_this_month, CACHE_5_MIN)

    # ── Latest attendance ─────────────────────────────────────────────────────
    latest_service = cache.get(f'dash_latest_service_{cid}')
    if latest_service is None:
        latest_service = ServiceAttendance.objects.filter(church=church).first()
        cache.set(f'dash_latest_service_{cid}', latest_service, CACHE_5_MIN)
    latest_attendance = latest_service.grand_total if latest_service else 0

    # ── Finance totals (heaviest queries — use DB aggregation not Python sum) ─
    total_contributions = cache.get(f'dash_total_contributions_{cid}')
    if total_contributions is None:
        # Use DB-level aggregation instead of looping in Python
        offerings = ServiceOffering.objects.filter(church=church)
        agg = offerings.aggregate(
            s1=Sum('first_offering'),
            s2=Sum('second_offering'),
            s3=Sum('jy_offering'),
            s4=Sum('children_offering'),
            s5=Sum('tithe'),
            s6=Sum('thanksgiving'),
            s7=Sum('other_amount'),
        )
        total_contributions = sum(v or 0 for v in agg.values())
        cache.set(f'dash_total_contributions_{cid}', total_contributions, CACHE_10_MIN)

    this_month_contributions = cache.get(f'dash_month_contributions_{cid}')
    if this_month_contributions is None:
        month_offerings = ServiceOffering.objects.filter(
            church=church, date__gte=this_month_start
        )
        agg = month_offerings.aggregate(
            s1=Sum('first_offering'),
            s2=Sum('second_offering'),
            s3=Sum('jy_offering'),
            s4=Sum('children_offering'),
            s5=Sum('tithe'),
            s6=Sum('thanksgiving'),
            s7=Sum('other_amount'),
        )
        this_month_contributions = sum(v or 0 for v in agg.values())
        cache.set(f'dash_month_contributions_{cid}', this_month_contributions, CACHE_10_MIN)

    return {
        'total_members':            total_members,
        'new_members_this_month':   new_members_this_month,
        'latest_service':           latest_service,
        'latest_attendance':        latest_attendance,
        'total_contributions':      total_contributions,
        'this_month_contributions': this_month_contributions,
    }


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    template_name = 'dashboard/index.html'

    def get(self, request):
        church           = request.user.church
        today            = date.today()
        this_month_start = today.replace(day=1)

        # Greeting — cheap, no caching needed
        current_hour = datetime.now().hour
        if current_hour < 12:
            greeting = "morning"
        elif current_hour < 17:
            greeting = "afternoon"
        else:
            greeting = "evening"

        # Cached stats
        stats = _get_dashboard_stats(church, today, this_month_start)

        # Recent lists — short cache, users expect these to be fresh
        cid = church.id

        upcoming_events = cache.get(f'dash_upcoming_events_{cid}')
        if upcoming_events is None:
            upcoming_events = list(
                Event.objects.filter(church=church, date__gte=today).order_by('date')[:5]
            )
            cache.set(f'dash_upcoming_events_{cid}', upcoming_events, CACHE_1_MIN)

        recent_members = cache.get(f'dash_recent_members_{cid}')
        if recent_members is None:
            recent_members = list(
                Member.objects.filter(church=church).order_by('-created_at')[:5]
            )
            cache.set(f'dash_recent_members_{cid}', recent_members, CACHE_1_MIN)

        recent_offerings = cache.get(f'dash_recent_offerings_{cid}')
        if recent_offerings is None:
            recent_offerings = list(
                ServiceOffering.objects.filter(church=church).order_by('-date')[:5]
            )
            cache.set(f'dash_recent_offerings_{cid}', recent_offerings, CACHE_1_MIN)

        context = {
            'greeting':         greeting,
            'upcoming_events':  upcoming_events,
            'recent_members':   recent_members,
            'recent_offerings': recent_offerings,
            **stats,
        }
        return render(request, self.template_name, context)

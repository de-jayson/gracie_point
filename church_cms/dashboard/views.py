"""Dashboard Views"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from datetime import date, datetime
from members.models import Member
from attendance.models import ServiceAttendance
from finance.models import ServiceOffering
from events.models import Event




@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    template_name = 'dashboard/index.html'

    def get(self, request):
        church           = request.user.church
        today            = date.today()
        this_month_start = today.replace(day=1)

        # Greeting
        current_hour = datetime.now().hour
        if current_hour < 12:
            greeting = "morning"
        elif current_hour < 17:
            greeting = "afternoon"
        else:
            greeting = "evening"

        # Members — scoped to this church
        total_members         = Member.objects.filter(church=church, status='active').count()
        new_members_this_month = Member.objects.filter(church=church, date_joined__gte=this_month_start).count()

        # Latest service attendance — scoped to this church
        latest_service    = ServiceAttendance.objects.filter(church=church).first()
        latest_attendance = latest_service.grand_total if latest_service else 0

        # Finance totals — scoped to this church
        all_offerings = ServiceOffering.objects.filter(church=church)
        total_contributions      = sum(r.total for r in all_offerings)
        this_month_contributions = sum(
            r.total for r in all_offerings.filter(date__gte=this_month_start)
        )

        # Events — scoped to this church
        upcoming_events = Event.objects.filter(church=church, date__gte=today).order_by('date')[:5]

        # Recent members — scoped to this church
        recent_members = Member.objects.filter(church=church).order_by('-created_at')[:5]

        # Recent offerings — scoped to this church
        recent_offerings = all_offerings.order_by('-date')[:5]

        context = {
            'greeting':                greeting,
            'total_members':           total_members,
            'new_members_this_month':  new_members_this_month,
            'latest_attendance':       latest_attendance,
            'latest_service':          latest_service,
            'total_contributions':     total_contributions,
            'this_month_contributions': this_month_contributions,
            'upcoming_events':         upcoming_events,
            'recent_members':          recent_members,
            'recent_offerings':        recent_offerings,
        }
        return render(request, self.template_name, context)

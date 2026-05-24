"""Dashboard Views — updated to use new attendance + finance models."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from  django.utils import timezone
from datetime import date, datetime
from members.models import Member
from attendance.models import ServiceAttendance
from finance.models import ServiceOffering
from events.models import Event




@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    template_name = 'dashboard/index.html'

    def get(self, request):
        today = date.today()
        this_month_start = today.replace(day=1)

        # 🟢 Greeting logic (FIX)
        current_hour = datetime.now().hour

        if current_hour < 12:
            greeting = "morning"
        elif current_hour < 17:
            greeting = "afternoon"
        else:
            greeting = "evening"

        # Members
        total_members = Member.objects.filter(status='active').count()
        new_members_this_month = Member.objects.filter(date_joined__gte=this_month_start).count()

        # Latest service attendance
        latest_service = ServiceAttendance.objects.first()
        latest_attendance = latest_service.grand_total if latest_service else 0

        # Finance totals
        all_offerings = list(ServiceOffering.objects.all())
        total_contributions = sum(r.total for r in all_offerings)
        this_month_contributions = sum(
            r.total for r in ServiceOffering.objects.filter(date__gte=this_month_start)
        )

        # Events
        upcoming_events = Event.objects.filter(date__gte=today).order_by('date')[:5]

        # Recent members
        recent_members = Member.objects.order_by('-created_at')[:5]

        # Recent offering records
        recent_offerings = ServiceOffering.objects.order_by('-date')[:5]

        context = {
            'greeting': greeting,
            'total_members': total_members,
            'new_members_this_month': new_members_this_month,
            'latest_attendance': latest_attendance,
            'latest_service': latest_service,
            'total_contributions': total_contributions,
            'this_month_contributions': this_month_contributions,
            'upcoming_events': upcoming_events,
            'recent_members': recent_members,
            'recent_offerings': recent_offerings,
        }
        return render(request, self.template_name, context)

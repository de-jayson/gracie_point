"""
Attendance Views
Headcount-based service attendance (no per-member tracking).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from .models import ServiceAttendance
from .forms import ServiceAttendanceForm
from dashboard.cache_utils import bust_attendance_cache


@method_decorator(login_required, name='dispatch')
class AttendanceListView(View):
    template_name = 'attendance/attendance_list.html'

    def get(self, request):
        records = ServiceAttendance.objects.filter(church=request.user.church)
        return render(request, self.template_name, {'records': records})


@method_decorator(login_required, name='dispatch')
class AttendanceCreateView(View):
    template_name = 'attendance/attendance_form.html'

    def get(self, request):
        form = ServiceAttendanceForm()
        return render(request, self.template_name, {'form': form, 'title': 'Record Attendance'})

    def post(self, request):
        form = ServiceAttendanceForm(request.POST)
        if form.is_valid():
            record        = form.save(commit=False)
            record.church = request.user.church
            record.save()
            bust_attendance_cache(request.user.church)   # ← new attendance record
            messages.success(request, f'Attendance for "{record.event_name}" saved. Total: {record.grand_total}')
            return redirect('attendance:list')
        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {'form': form, 'title': 'Record Attendance'})


@method_decorator(login_required, name='dispatch')
class AttendanceEditView(View):
    template_name = 'attendance/attendance_form.html'

    def get(self, request, pk):
        record = get_object_or_404(ServiceAttendance, pk=pk, church=request.user.church)
        form   = ServiceAttendanceForm(instance=record)
        return render(request, self.template_name, {'form': form, 'title': 'Edit Attendance', 'record': record})

    def post(self, request, pk):
        record = get_object_or_404(ServiceAttendance, pk=pk, church=request.user.church)
        form   = ServiceAttendanceForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            bust_attendance_cache(request.user.church)   # ← attendance figures changed
            messages.success(request, 'Attendance record updated.')
            return redirect('attendance:list')
        return render(request, self.template_name, {'form': form, 'title': 'Edit Attendance', 'record': record})


@method_decorator(login_required, name='dispatch')
class AttendanceDetailView(View):
    template_name = 'attendance/attendance_detail.html'

    def get(self, request, pk):
        record = get_object_or_404(ServiceAttendance, pk=pk, church=request.user.church)
        return render(request, self.template_name, {'record': record})


@method_decorator(login_required, name='dispatch')
class AttendanceDeleteView(View):

    def post(self, request, pk):
        record = get_object_or_404(ServiceAttendance, pk=pk, church=request.user.church)
        record.delete()
        bust_attendance_cache(request.user.church)       # ← record removed
        messages.success(request, 'Attendance record deleted.')
        return redirect('attendance:list')

"""
Members Views
Full CRUD for church member management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db.models import Q
from .models import Member
from .forms import MemberForm


@method_decorator(login_required, name='dispatch')
class MemberListView(View):
    """Lists all members with search, filter, and sort support."""
    template_name = 'members/member_list.html'

    def get(self, request):
        query     = request.GET.get('q', '')
        sort      = request.GET.get('sort', 'first_name')
        direction = request.GET.get('dir', 'asc')
        status    = request.GET.get('status', '')

        members = Member.objects.filter(church=request.user.church)

        if query:
            members = members.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)  |
                Q(phone__icontains=query)      |
                Q(email__icontains=query)
            )

        if status:
            members = members.filter(status=status)

        allowed_sorts = ['first_name', 'date_joined', 'status', 'name']
        if sort not in allowed_sorts:
            sort = 'first_name'

        if sort == 'name':
            order_fields = ['first_name', 'last_name']
        else:
            order_fields = [sort]

        if direction == 'desc':
            order_fields = [f'-{field}' for field in order_fields]

        members = members.order_by(*order_fields)

        return render(request, self.template_name, {
            'members':        members,
            'current_sort':   sort,
            'current_dir':    direction,
            'query':          query,
            'current_status': status,
            'total_count':    members.count(),
        })


@method_decorator(login_required, name='dispatch')
class MemberDetailView(View):
    template_name = 'members/member_detail.html'

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk, church=request.user.church)
        return render(request, self.template_name, {
            'member':             member,
            'attendance_records': [],
            'contributions':      [],
        })


@method_decorator(login_required, name='dispatch')
class MemberCreateView(View):
    """Creates a new member and assigns them to this church."""
    template_name = 'members/member_form.html'

    def get(self, request):
        form = MemberForm()
        return render(request, self.template_name, {'form': form, 'title': 'Add Member'})

    def post(self, request):
        form = MemberForm(request.POST)
        if form.is_valid():
            member        = form.save(commit=False)       # hold before saving
            member.church = request.user.church           # auto-assign church
            member.save()                                 # now write to DB
            messages.success(request, f'{member.full_name} has been added successfully.')
            return redirect('members:detail', pk=member.pk)
        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {'form': form, 'title': 'Add Member'})


@method_decorator(login_required, name='dispatch')
class MemberEditView(View):
    """Edits an existing member within this church."""
    template_name = 'members/member_form.html'

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk, church=request.user.church)
        form   = MemberForm(instance=member)
        return render(request, self.template_name, {'form': form, 'title': 'Edit Member', 'member': member})

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk, church=request.user.church)
        form   = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'{member.full_name} has been updated successfully.')
            return redirect('members:detail', pk=member.pk)
        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {'form': form, 'title': 'Edit Member', 'member': member})


@method_decorator(login_required, name='dispatch')
class MemberDeleteView(View):
    """Deletes a member within this church."""

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk, church=request.user.church)
        name   = member.full_name
        member.delete()
        messages.success(request, f'{name} has been removed from the system.')
        return redirect('members:list')

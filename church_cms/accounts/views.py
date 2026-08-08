"""
Accounts Views
Handles login, logout, and user management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from .forms import LoginForm, CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from .decorators import admin_required
from django.views.generic import CreateView


class LoginView(View):
    """Handles user login via email + password."""
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST, request=request)   # ← pass request for authenticate()
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class LogoutView(View):
    """Handles user logout."""

    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('accounts:login')

    def get(self, request):
        logout(request)
        return redirect('accounts:login')


@method_decorator([login_required, admin_required], name='dispatch')
class UserListView(View):
    """Lists all users belonging to the same church. Admin only."""
    template_name = 'accounts/user_list.html'

    def get(self, request):
        users = CustomUser.objects.filter(church=request.user.church).order_by('username')
        return render(request, self.template_name, {'users': users})


@method_decorator([login_required, admin_required], name='dispatch')
class UserCreateView(CreateView
                     ):
    """Creates a new user and auto-assigns them to the admin's church. Admin only."""
    template_name = 'accounts/user_form.html'
    model = CustomUser
    fields = ['username', 'email', 'role']

    def get(self, request):
        form = CustomUserCreationForm()
        
        return render(request, self.template_name, {'form': form, 'title': 'Add User'})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            # Automatically assign user to the admin's church
            user.church = request.user.church

            # Prevent creating another church administrator
            if user.role == CustomUser.Role.CHURCH_ADMIN:
                messages.error(
                    request,
                    'A church already has an administrator. You can only create Pastor, Finance Officer, or Secretary accounts.'
                )
                return render(request, self.template_name, {
                    'form': form,
                    'title': 'Add User'
                })

            user.save()

            messages.success(request, 'User created successfully.')
            return redirect('accounts:user_list')

        return render(request, self.template_name, {
            'form': form,
            'title': 'Add User'
        })

@method_decorator([login_required, admin_required], name='dispatch')
class UserEditView(View):
    """Edits a user within the same church. Admin only."""
    template_name = 'accounts/user_form.html'

    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk, church=request.user.church)
        form = CustomUserChangeForm(instance=user)
        return render(request, self.template_name, {'form': form, 'title': 'Edit User', 'edit_user': user})

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk, church=request.user.church)
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('accounts:user_list')
        return render(request, self.template_name, {'form': form, 'title': 'Edit User', 'edit_user': user})


@method_decorator([login_required, admin_required], name='dispatch')
class UserDeleteView(View):
    """Deletes a user within the same church. Admin only. Cannot delete own account."""

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk, church=request.user.church)
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
        else:
            user.delete()
            messages.success(request, 'User deleted successfully.')
        return redirect('accounts:user_list')

"""
Accounts Views
Handles login, logout, and user management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from .forms import LoginForm, CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from .decorators import admin_required


class LoginView(View):
    """Handles user login."""
    template_name = 'accounts/login.html'

    def get(self, request):
        # Redirect already logged-in users
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            # Redirect to 'next' param if present, else dashboard
            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class LogoutView(View):
    """Handles user logout."""

    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('accounts:login')

    def get(self, request):
        # Allow GET for simplicity
        logout(request)
        return redirect('accounts:login')


@method_decorator([login_required, admin_required], name='dispatch')
class UserListView(View):
    """Lists all system users. Admin only."""
    template_name = 'accounts/user_list.html'

    def get(self, request):
        users = CustomUser.objects.all().order_by('username')
        return render(request, self.template_name, {'users': users})


@method_decorator([login_required, admin_required], name='dispatch')
class UserCreateView(View):
    """Creates a new system user. Admin only."""
    template_name = 'accounts/user_form.html'

    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, self.template_name, {'form': form, 'title': 'Add User'})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('accounts:user_list')
        return render(request, self.template_name, {'form': form, 'title': 'Add User'})


@method_decorator([login_required, admin_required], name='dispatch')
class UserEditView(View):
    """Edits an existing user. Admin only."""
    template_name = 'accounts/user_form.html'

    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        form = CustomUserChangeForm(instance=user)
        return render(request, self.template_name, {'form': form, 'title': 'Edit User', 'edit_user': user})

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('accounts:user_list')
        return render(request, self.template_name, {'form': form, 'title': 'Edit User', 'edit_user': user})


@method_decorator([login_required, admin_required], name='dispatch')
class UserDeleteView(View):
    """Deletes a user. Admin only. Cannot delete own account."""

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
        else:
            user.delete()
            messages.success(request, 'User deleted successfully.')
        return redirect('accounts:user_list')

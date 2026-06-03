from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Church
from .forms import ChurchRegistrationForm

User = get_user_model()


@transaction.atomic
def register_church(request):
    if request.method == "POST":
        form = ChurchRegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Step 1: Create the Church
            church = Church.objects.create(
                name=data['church_name'],
                email=data['church_email'],
                phone=data.get('church_phone', ''),
                address=data.get('church_address', ''),
            )

            # Step 2: Create the Administrator using their chosen username
            User.objects.create_user(
                username=data['admin_username'],
                email=data['admin_email'],
                password=data['admin_password'],
                full_name=data['admin_full_name'],
                church=church,
                role='church_admin',
                is_church_admin=True,
            )

            _setup_church_defaults(church)

            messages.success(
                request,
                f'"{church.name}" workspace created! Log in with username: {data["admin_username"]}',
            )
            return redirect('accounts:login')

    else:
        form = ChurchRegistrationForm()

    return render(request, 'organizations/register.html', {'form': form})


def _setup_church_defaults(church):
    pass

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import CustomUserCreationForm
from users.models import ActivityLog


def get_client_ip(request):
    """Extract real client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please login now.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    # Already logged in → skip the login page
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Log successful login with IP
            ActivityLog.objects.create(
                user=user,
                action='login',
                success=True,
                ip_address=get_client_ip(request),
                details=f"Successful login for {user.username}",
            )

            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            # Log failed login attempt — user=None is now allowed
            ActivityLog.objects.create(
                user=None,
                action='failed_login',
                success=False,
                ip_address=get_client_ip(request),
                details="Failed login attempt with invalid credentials",
            )
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    username = request.user.username
    ActivityLog.objects.create(
        user=request.user,
        action='logout',
        success=True,
        ip_address=get_client_ip(request),
        details=f"User {username} logged out",
    )
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')
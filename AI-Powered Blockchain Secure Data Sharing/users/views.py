from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import CustomUserCreationForm

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
    # If user is already properly logged in, go to dashboard
    if request.user.is_authenticated:
        return redirect('my_files')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('my_files')
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')
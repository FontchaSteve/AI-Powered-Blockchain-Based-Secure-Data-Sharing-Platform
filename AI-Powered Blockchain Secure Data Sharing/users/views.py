from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm
from users.models import ActivityLog, CustomUser


def get_client_ip(request):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    if x:
        return x.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def auto_assign_wallet(user):
    """Automatically assign the next free Ganache account to a new user."""
    try:
        from blockchain.contract_interaction import get_web3
        w3 = get_web3()
        if not w3.is_connected():
            return
        all_accounts = list(w3.eth.accounts)
        taken_lower = {
            a.lower() for a in
            CustomUser.objects.exclude(wallet_address=None)
            .values_list('wallet_address', flat=True) if a
        }
        for account in all_accounts:
            if account.lower() not in taken_lower:
                user.wallet_address = account
                user.save(update_fields=['wallet_address'])
                return
    except Exception:
        pass


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auto_assign_wallet(user)
            messages.success(request, "Account created! Please log in.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            ActivityLog.objects.create(
                user=user, action='login', success=True,
                ip_address=get_client_ip(request),
                details=f"Login: {user.username}",
            )
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            ActivityLog.objects.create(
                user=None, action='failed_login', success=False,
                ip_address=get_client_ip(request),
                details="Failed login attempt",
            )
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    ActivityLog.objects.create(
        user=request.user, action='logout', success=True,
        ip_address=get_client_ip(request),
        details=f"Logout: {request.user.username}",
    )
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_email':
            new_email = request.POST.get('email', '').strip()
            if not new_email:
                messages.error(request, "Email cannot be empty.")
            elif CustomUser.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                messages.error(request, "That email is already in use.")
            else:
                user.email = new_email
                user.save(update_fields=['email'])
                messages.success(request, "Email updated.")
            return redirect('profile')

        if action == 'change_password':
            pw_form = PasswordChangeForm(user, request.POST)
            if pw_form.is_valid():
                pw_form.save()
                update_session_auth_hash(request, pw_form.user)
                messages.success(request, "Password changed.")
            else:
                for errors in pw_form.errors.values():
                    for error in errors:
                        messages.error(request, error)
            return redirect('profile')

    from files.models import File, FileShare
    from files.ipfs_utils import is_pinata_configured

    ganache_connected = False
    wallet_balance    = None
    try:
        from blockchain.contract_interaction import get_web3
        w3 = get_web3()
        if w3.is_connected():
            ganache_connected = True
            if user.wallet_address:
                bal = w3.eth.get_balance(user.wallet_address)
                wallet_balance = round(float(w3.from_wei(bal, 'ether')), 4)
    except Exception:
        pass

    context = {
        'total_files':       File.objects.filter(owner=user).count(),
        'total_shared':      FileShare.objects.filter(shared_by=user).count(),
        'total_received':    FileShare.objects.filter(shared_with=user).count(),
        'total_logins':      ActivityLog.objects.filter(user=user, action='login').count(),
        'ganache_connected': ganache_connected,
        'wallet_balance':    wallet_balance,
        'ipfs_enabled':      is_pinata_configured(),
    }
    return render(request, 'users/profile.html', context)
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


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
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

        # ── Update wallet address ──
        if action == 'update_wallet':
            wallet = request.POST.get('wallet_address', '').strip()

            if wallet:
                # Validate format
                if not (wallet.startswith('0x') and len(wallet) == 42):
                    messages.error(
                        request,
                        "Invalid wallet address — must start with 0x and be 42 characters."
                    )
                    return redirect('profile')

                # ── WALLET COLLISION CHECK ──
                # Check if another user already has this wallet address
                conflict = CustomUser.objects.filter(
                    wallet_address__iexact=wallet
                ).exclude(pk=user.pk).first()

                if conflict:
                    messages.error(
                        request,
                        f"⚠ That wallet address is already registered by another user. "
                        f"Each user must use a different Ganache account. "
                        f"Please pick a different account from the list."
                    )
                    return redirect('profile')

            # Save (wallet can be empty string → clears it)
            user.wallet_address = wallet or None
            user.save(update_fields=['wallet_address'])
            if wallet:
                messages.success(request, f"✅ Wallet connected: {wallet[:10]}…{wallet[-4:]}")
            else:
                messages.success(request, "Wallet address cleared.")
            return redirect('profile')

        # ── Update email ──
        if action == 'update_email':
            new_email = request.POST.get('email', '').strip()
            if not new_email:
                messages.error(request, "Email cannot be empty.")
            elif CustomUser.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                messages.error(request, "That email is already in use.")
            else:
                user.email = new_email
                user.save(update_fields=['email'])
                messages.success(request, "✅ Email updated.")
            return redirect('profile')

        # ── Change password ──
        if action == 'change_password':
            pw_form = PasswordChangeForm(user, request.POST)
            if pw_form.is_valid():
                pw_form.save()
                update_session_auth_hash(request, pw_form.user)
                messages.success(request, "✅ Password changed.")
            else:
                for errors in pw_form.errors.values():
                    for error in errors:
                        messages.error(request, error)
            return redirect('profile')

    # ── Build context ──
    from files.models import File, FileShare
    from files.ipfs_utils import is_pinata_configured

    total_files    = File.objects.filter(owner=user).count()
    total_shared   = FileShare.objects.filter(shared_by=user).count()
    total_received = FileShare.objects.filter(shared_with=user).count()
    total_logins   = ActivityLog.objects.filter(user=user, action='login').count()
    ipfs_enabled   = is_pinata_configured()

    # Ganache info
    ganache_connected = False
    wallet_balance    = None
    ganache_accounts  = []

    try:
        from blockchain.contract_interaction import get_web3
        w3 = get_web3()
        if w3.is_connected():
            ganache_connected = True
            ganache_accounts  = list(w3.eth.accounts)
            if user.wallet_address:
                bal_wei        = w3.eth.get_balance(user.wallet_address)
                wallet_balance = round(float(w3.from_wei(bal_wei, 'ether')), 4)
    except Exception:
        pass

    # ── Mark which accounts are already taken by other users ──
    # Maps wallet_address (lowercase) → username of the user who owns it
    taken_wallets = {}
    for u in CustomUser.objects.exclude(pk=user.pk).exclude(wallet_address=None):
        if u.wallet_address:
            taken_wallets[u.wallet_address.lower()] = u.username

    # Build enriched account list for the template
    account_info = []
    for addr in ganache_accounts:
        owner_username = taken_wallets.get(addr.lower())
        is_mine        = (
            user.wallet_address and
            user.wallet_address.lower() == addr.lower()
        )
        try:
            bal = float(w3.from_wei(w3.eth.get_balance(addr), 'ether')) if ganache_connected else None
        except Exception:
            bal = None

        account_info.append({
            'address':        addr,
            'is_mine':        is_mine,
            'taken_by':       owner_username,   # None if free
            'is_taken':       owner_username is not None,
            'balance':        round(bal, 2) if bal is not None else None,
        })

    context = {
        'total_files':       total_files,
        'total_shared':      total_shared,
        'total_received':    total_received,
        'total_logins':      total_logins,
        'ganache_connected': ganache_connected,
        'wallet_balance':    wallet_balance,
        'account_info':      account_info,
        'ipfs_enabled':      ipfs_enabled,
    }
    return render(request, 'users/profile.html', context)
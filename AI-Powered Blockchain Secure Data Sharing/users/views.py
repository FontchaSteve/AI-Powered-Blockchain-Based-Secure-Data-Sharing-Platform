from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .forms import CustomUserCreationForm
from users.models import ActivityLog, CustomUser


def get_client_ip(request):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    if x:
        return x.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def auto_assign_wallet(user):
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


# ====================== CUSTOM ADMIN PANEL ======================
def admin_required(view_func):
    """Decorator — only superusers can access."""
    return user_passes_test(lambda u: u.is_active and u.is_superuser)(
        login_required(view_func)
    )


@admin_required
def admin_dashboard(request):
    from files.models import File, FileShare
    context = {
        'total_users':    CustomUser.objects.count(),
        'total_files':    File.objects.count(),
        'total_shares':   FileShare.objects.count(),
        'total_logs':     ActivityLog.objects.count(),
        'recent_users':   CustomUser.objects.order_by('-date_joined')[:5],
        'recent_logs':    ActivityLog.objects.order_by('-timestamp')[:10],
        'failed_logins':  ActivityLog.objects.filter(action='failed_login').count(),
        'uploads_today':  ActivityLog.objects.filter(
                              action='upload',
                              timestamp__date=timezone.now().date()
                          ).count(),
        'all_users':      CustomUser.objects.order_by('-date_joined'),
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def admin_user_detail(request, user_id):
    from files.models import File, FileShare
    target = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_active':
            if target == request.user:
                messages.error(request, "You cannot deactivate your own account.")
            else:
                target.is_active = not target.is_active
                target.save(update_fields=['is_active'])
                status = "activated" if target.is_active else "deactivated"
                messages.success(request, f"User {target.username} {status}.")
            return redirect('admin_user_detail', user_id=user_id)

        if action == 'toggle_staff':
            target.is_staff = not target.is_staff
            target.save(update_fields=['is_staff'])
            messages.success(request, f"Staff status updated for {target.username}.")
            return redirect('admin_user_detail', user_id=user_id)

        if action == 'delete_user':
            if target == request.user:
                messages.error(request, "You cannot delete your own account.")
            else:
                username = target.username
                target.delete()
                messages.success(request, f"User '{username}' deleted.")
                return redirect('admin_dashboard')
            return redirect('admin_user_detail', user_id=user_id)

        if action == 'reset_wallet':
            auto_assign_wallet(target)
            messages.success(request, f"Wallet reassigned for {target.username}.")
            return redirect('admin_user_detail', user_id=user_id)

    context = {
        'target':      target,
        'files':       File.objects.filter(owner=target).order_by('-upload_date'),
        'shares_given':FileShare.objects.filter(shared_by=target),
        'shares_recv': FileShare.objects.filter(shared_with=target),
        'logs':        ActivityLog.objects.filter(user=target).order_by('-timestamp')[:20],
    }
    return render(request, 'admin_panel/user_detail.html', context)


@admin_required
def admin_delete_file(request, file_id):
    from files.models import File
    import os
    from files.ipfs_utils import unpin_from_ipfs
    file_obj = get_object_or_404(File, id=file_id)
    if request.method == 'POST':
        owner_id = file_obj.owner.id
        if file_obj.ipfs_cid:
            unpin_from_ipfs(file_obj.ipfs_cid)
        if file_obj.encrypted_file_path and os.path.exists(file_obj.encrypted_file_path):
            os.remove(file_obj.encrypted_file_path)
        filename = file_obj.filename
        file_obj.delete()
        messages.success(request, f"File '{filename}' deleted.")
        return redirect('admin_user_detail', user_id=owner_id)
    return redirect('admin_dashboard')


@admin_required
def admin_dashboard(request):
    from files.models import File, FileShare

    all_users = CustomUser.objects.prefetch_related('owned_files').order_by('-date_joined')
    all_files = File.objects.select_related('owner').order_by('-upload_date')

    context = {
        # Stats
        'total_users':    CustomUser.objects.count(),
        'active_users':   CustomUser.objects.filter(is_active=True).count(),
        'banned_users':   CustomUser.objects.filter(is_active=False).count(),
        'total_files':    File.objects.count(),
        'ipfs_files':     File.objects.exclude(ipfs_cid=None).exclude(ipfs_cid='').count(),
        'local_files':    File.objects.filter(ipfs_cid=None).count(),
        'total_shares':   FileShare.objects.count(),
        'total_logs':     ActivityLog.objects.count(),
        'failed_logins':  ActivityLog.objects.filter(action='failed_login').count(),
        'uploads_today':  ActivityLog.objects.filter(
                              action='upload',
                              timestamp__date=timezone.now().date()
                          ).count(),
        # Table data
        'all_users':      all_users,
        'all_files':      all_files,
        'recent_logs':    ActivityLog.objects.select_related('user').order_by('-timestamp')[:200],
        # Tabs definition for template
        'tabs': [
            ('users',    'Users',    'people-fill'),
            ('files',    'Files',    'file-earmark-lock-fill'),
            ('activity', 'Activity', 'activity'),
        ],
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def admin_user_detail(request, user_id):
    from files.models import File, FileShare
    target = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_active':
            if target == request.user:
                messages.error(request, "You cannot deactivate your own account.")
            else:
                target.is_active = not target.is_active
                target.save(update_fields=['is_active'])
                status = "activated" if target.is_active else "banned"
                messages.success(request, f"User {target.username} {status}.")
            return redirect('admin_user_detail', user_id=user_id)

        if action == 'toggle_staff':
            target.is_staff = not target.is_staff
            target.save(update_fields=['is_staff'])
            messages.success(request, f"Staff status updated for {target.username}.")
            return redirect('admin_user_detail', user_id=user_id)

        if action == 'delete_user':
            if target == request.user:
                messages.error(request, "You cannot delete your own account.")
            else:
                username = target.username
                target.delete()
                messages.success(request, f"User '{username}' deleted.")
                return redirect('admin_dashboard')
            return redirect('admin_user_detail', user_id=user_id)

        if action == 'reset_wallet':
            auto_assign_wallet(target)
            messages.success(request, f"Wallet reassigned for {target.username}.")
            return redirect('admin_user_detail', user_id=user_id)

    context = {
        'target':       target,
        'files':        File.objects.filter(owner=target).order_by('-upload_date'),
        'shares_given': FileShare.objects.filter(shared_by=target).select_related('shared_with', 'file'),
        'shares_recv':  FileShare.objects.filter(shared_with=target).select_related('shared_by', 'file'),
        'logs':         ActivityLog.objects.filter(user=target).order_by('-timestamp')[:30],
        'total_downloads': ActivityLog.objects.filter(user=target, action='download').count(),
        'total_uploads':   ActivityLog.objects.filter(user=target, action='upload').count(),
        'total_logins':    ActivityLog.objects.filter(user=target, action='login').count(),
    }
    return render(request, 'admin_panel/user_detail.html', context)


@admin_required
def admin_delete_file(request, file_id):
    from files.models import File
    import os
    from files.ipfs_utils import unpin_from_ipfs
    file_obj = get_object_or_404(File, id=file_id)
    if request.method == 'POST':
        owner_id = file_obj.owner.id
        if file_obj.ipfs_cid:
            unpin_from_ipfs(file_obj.ipfs_cid)
        if file_obj.encrypted_file_path and os.path.exists(file_obj.encrypted_file_path):
            os.remove(file_obj.encrypted_file_path)
        filename = file_obj.filename
        file_obj.delete()
        messages.success(request, f"File '{filename}' deleted.")
        return redirect('admin_user_detail', user_id=owner_id)
    return redirect('admin_dashboard')


@admin_required
def admin_export_logs(request):
    """Export all activity logs as a CSV file."""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="secureshare_activity_logs.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Username', 'Action', 'Success', 'IP Address', 'Details', 'File Hash'])

    for log in ActivityLog.objects.select_related('user').order_by('-timestamp'):
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else 'Anonymous',
            log.action,
            'Yes' if log.success else 'No',
            log.ip_address or '',
            log.details or '',
            log.file_hash or '',
        ])

    return response
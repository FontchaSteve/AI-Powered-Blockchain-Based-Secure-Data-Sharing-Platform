from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
import os

from .forms import FileUploadForm
from .encryption_utils import generate_file_hash, encrypt_file, save_encrypted_file, decrypt_file
from .models import File, FileShare
from blockchain.contract_interaction import get_contract
from users.models import ActivityLog, CustomUser


def get_client_ip(request):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    if x:
        return x.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ====================== DASHBOARD ======================
@login_required
def dashboard(request):
    recent_files  = File.objects.filter(owner=request.user).order_by('-upload_date')[:6]
    total_files   = File.objects.filter(owner=request.user).count()
    shared_with_me = FileShare.objects.filter(shared_with=request.user).count()
    recent_activity = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:8]

    context = {
        'recent_files':    recent_files,
        'total_files':     total_files,
        'shared_with_me':  shared_with_me,
        'recent_activity': recent_activity,
    }
    return render(request, 'files/dashboard.html', context)


# ====================== UPLOAD ======================
@login_required
def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            file_data = uploaded_file.read()

            file_hash = generate_file_hash(file_data)

            if File.objects.filter(file_hash=file_hash).exists():
                messages.warning(request, "This file already exists in your vault.")
                return redirect('my_files')

            encrypted_data, encryption_key = encrypt_file(file_data)
            encrypted_filename = f"enc_{file_hash[:16]}_{uploaded_file.name}"
            file_path = save_encrypted_file(encrypted_data, encrypted_filename)

            try:
                w3, contract = get_contract()
                account = w3.eth.accounts[0]
                tx = contract.functions.uploadFile(file_hash).build_transaction({
                    'from': account,
                    'nonce': w3.eth.get_transaction_count(account),
                    'gas': 2000000,
                })
                tx_hash = w3.eth.send_transaction(tx)
                w3.eth.wait_for_transaction_receipt(tx_hash)
                tx_hash_hex = tx_hash.hex()
                messages.success(request, "✅ File encrypted and registered on blockchain!")
            except Exception as e:
                tx_hash_hex = None
                messages.warning(request, f"File saved but blockchain registration failed: {str(e)}")

            File.objects.create(
                owner=request.user,
                filename=uploaded_file.name,
                original_filename=uploaded_file.name,
                file_hash=file_hash,
                encrypted_file_path=file_path,
                encryption_key=encryption_key,
                blockchain_tx_hash=tx_hash_hex,
            )

            ActivityLog.objects.create(
                user=request.user,
                action='upload',
                file_hash=file_hash,
                success=True,
                ip_address=get_client_ip(request),
                details=f"File uploaded: {uploaded_file.name}",
            )
            return redirect('dashboard')
    else:
        form = FileUploadForm()

    return render(request, 'files/upload.html', {'form': form})


# ====================== DOWNLOAD (owner) ======================
@login_required
def download_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id, owner=request.user)
    return _do_download(request, file_obj)


# ====================== DOWNLOAD SHARED ======================
@login_required
def download_shared_file(request, file_id):
    """Allow a user who received a share to download the file."""
    share = get_object_or_404(FileShare, file_id=file_id, shared_with=request.user, can_download=True)
    if share.is_expired():
        messages.error(request, "This share link has expired.")
        return redirect('shared_with_me')
    return _do_download(request, share.file)


def _do_download(request, file_obj):
    try:
        with open(file_obj.encrypted_file_path, 'rb') as f:
            encrypted_data = f.read()
        key_bytes    = bytes(file_obj.encryption_key)
        decrypted    = decrypt_file(encrypted_data, key_bytes)

        ActivityLog.objects.create(
            user=request.user,
            action='download',
            file_hash=file_obj.file_hash,
            success=True,
            ip_address=get_client_ip(request),
            details=f"Downloaded: {file_obj.filename}",
        )
        response = HttpResponse(decrypted, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_obj.original_filename}"'
        return response

    except FileNotFoundError:
        messages.error(request, "Encrypted file not found on disk.")
        ActivityLog.objects.create(
            user=request.user, action='download', file_hash=file_obj.file_hash,
            success=False, ip_address=get_client_ip(request),
            details=f"Download failed — not found: {file_obj.filename}",
        )
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Download error: {str(e)}")
        return redirect('dashboard')


# ====================== DELETE ======================
@login_required
def delete_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id, owner=request.user)
    if request.method != 'POST':
        return redirect('dashboard')

    file_hash = file_obj.file_hash
    filename  = file_obj.filename

    if os.path.exists(file_obj.encrypted_file_path):
        os.remove(file_obj.encrypted_file_path)
    file_obj.delete()

    ActivityLog.objects.create(
        user=request.user, action='delete', file_hash=file_hash,
        success=True, ip_address=get_client_ip(request),
        details=f"Deleted: {filename}",
    )
    messages.success(request, f"'{filename}' deleted.")
    return redirect('my_files')


# ====================== MY FILES ======================
@login_required
def my_files(request):
    files = File.objects.filter(owner=request.user).order_by('-upload_date')
    return render(request, 'files/my_files.html', {'files': files})


# ====================== SHARE A FILE ======================
@login_required
def share_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id, owner=request.user)

    # Current shares for this file
    current_shares = FileShare.objects.filter(file=file_obj)

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Revoke a share ──
        if action == 'revoke':
            share_id = request.POST.get('share_id')
            share = get_object_or_404(FileShare, id=share_id, file=file_obj)
            username = share.shared_with.username
            share.delete()
            messages.success(request, f"Access revoked for {username}.")
            return redirect('share_file', file_id=file_id)

        # ── Grant a share ──
        username = request.POST.get('username', '').strip()
        if not username:
            messages.error(request, "Please enter a username.")
        elif username == request.user.username:
            messages.error(request, "You cannot share a file with yourself.")
        else:
            try:
                target_user = CustomUser.objects.get(username=username)
                share, created = FileShare.objects.get_or_create(
                    file=file_obj,
                    shared_with=target_user,
                    defaults={'shared_by': request.user},
                )
                if created:
                    ActivityLog.objects.create(
                        user=request.user, action='share',
                        file_hash=file_obj.file_hash, success=True,
                        ip_address=get_client_ip(request),
                        details=f"Shared '{file_obj.filename}' with {username}",
                    )
                    messages.success(request, f"✅ File shared with {username}!")
                else:
                    messages.warning(request, f"{username} already has access to this file.")
            except CustomUser.DoesNotExist:
                messages.error(request, f"No user found with username '{username}'.")

        return redirect('share_file', file_id=file_id)

    context = {
        'file': file_obj,
        'current_shares': current_shares,
    }
    return render(request, 'files/share_file.html', context)


# ====================== SHARED WITH ME ======================
@login_required
def shared_with_me(request):
    shares = FileShare.objects.filter(
        shared_with=request.user
    ).select_related('file', 'shared_by').order_by('-shared_at')
    return render(request, 'files/shared_with_me.html', {'shares': shares})


# ====================== BLOCKCHAIN VERIFY ======================
@login_required
def blockchain_verify(request):
    result = None
    file_hash = request.GET.get('hash', '').strip() or request.POST.get('file_hash', '').strip()

    if file_hash:
        # Check local DB
        try:
            db_file = File.objects.get(file_hash=file_hash)
        except File.DoesNotExist:
            db_file = None

        # Check blockchain
        blockchain_data = None
        blockchain_error = None
        try:
            w3, contract = get_contract()
            chain_file = contract.functions.files(file_hash).call()
            # chain_file = (fileHash, owner, uploadTime, isActive)
            if chain_file[3]:  # isActive
                import datetime
                blockchain_data = {
                    'file_hash':    chain_file[0],
                    'owner_wallet': chain_file[1],
                    'upload_time':  datetime.datetime.fromtimestamp(chain_file[2]),
                    'is_active':    chain_file[3],
                }
        except Exception as e:
            blockchain_error = str(e)

        result = {
            'file_hash':       file_hash,
            'db_file':         db_file,
            'blockchain_data': blockchain_data,
            'blockchain_error':blockchain_error,
            'verified':        (blockchain_data is not None),
        }

    # Pass user's own files for quick lookup
    my_files_list = File.objects.filter(owner=request.user).order_by('-upload_date')

    context = {
        'result':       result,
        'file_hash':    file_hash,
        'my_files':     my_files_list,
    }
    return render(request, 'blockchain/verify.html', context)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
import os
import datetime

from .forms import FileUploadForm
from .encryption_utils import generate_file_hash, encrypt_file, save_encrypted_file, decrypt_file
from .models import File, FileShare
from .ipfs_utils import upload_to_ipfs, download_from_ipfs, unpin_from_ipfs, is_pinata_configured
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
    recent_files    = File.objects.filter(owner=request.user).order_by('-upload_date')[:6]
    total_files     = File.objects.filter(owner=request.user).count()
    shared_with_me  = FileShare.objects.filter(shared_with=request.user).count()
    recent_activity = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:8]
    ipfs_enabled    = is_pinata_configured()

    context = {
        'recent_files':    recent_files,
        'total_files':     total_files,
        'shared_with_me':  shared_with_me,
        'recent_activity': recent_activity,
        'ipfs_enabled':    ipfs_enabled,
    }
    return render(request, 'files/dashboard.html', context)


# ====================== UPLOAD ======================
@login_required
def upload_file(request):
    ipfs_enabled = is_pinata_configured()

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            file_data     = uploaded_file.read()

            if len(file_data) > 50 * 1024 * 1024:
                messages.error(request, "File too large. Maximum size is 50 MB.")
                return redirect('upload_file')

            file_hash = generate_file_hash(file_data)

            if File.objects.filter(file_hash=file_hash).exists():
                messages.warning(request, "This exact file already exists in the vault.")
                return redirect('my_files')

            encrypted_data, encryption_key = encrypt_file(file_data)
            encrypted_filename = f"enc_{file_hash[:16]}_{uploaded_file.name}"

            ipfs_cid  = None
            file_path = ''

            if ipfs_enabled:
                try:
                    ipfs_cid    = upload_to_ipfs(encrypted_data, encrypted_filename)
                    storage_msg = f"☁ Stored on IPFS"
                except Exception as e:
                    messages.warning(request, f"IPFS upload failed, saved locally: {str(e)}")
                    file_path   = save_encrypted_file(encrypted_data, encrypted_filename)
                    storage_msg = "💾 Stored locally"
            else:
                file_path   = save_encrypted_file(encrypted_data, encrypted_filename)
                storage_msg = "💾 Stored locally"

            tx_hash_hex = None
            try:
                w3, contract = get_contract()
                account = request.user.wallet_address or w3.eth.accounts[0]
                tx = contract.functions.uploadFile(file_hash).build_transaction({
                    'from':  account,
                    'nonce': w3.eth.get_transaction_count(account),
                    'gas':   2000000,
                })
                tx_hash     = w3.eth.send_transaction(tx)
                w3.eth.wait_for_transaction_receipt(tx_hash)
                tx_hash_hex = tx_hash.hex()
                messages.success(request, f"✅ File encrypted, {storage_msg}, registered on blockchain!")
            except Exception as e:
                messages.warning(request, f"File saved ({storage_msg}) but blockchain failed: {str(e)}")

            File.objects.create(
                owner               = request.user,
                filename            = uploaded_file.name,
                original_filename   = uploaded_file.name,
                file_hash           = file_hash,
                encrypted_file_path = file_path,
                ipfs_cid            = ipfs_cid,
                encryption_key      = encryption_key,
                blockchain_tx_hash  = tx_hash_hex,
                file_size           = len(file_data),
                download_count      = 0,
            )

            ActivityLog.objects.create(
                user=request.user, action='upload', file_hash=file_hash,
                success=True, ip_address=get_client_ip(request),
                details=f"Uploaded: {uploaded_file.name}",
            )
            return redirect('dashboard')
    else:
        form = FileUploadForm()

    return render(request, 'files/upload.html', {'form': form, 'ipfs_enabled': ipfs_enabled})


# ====================== DOWNLOAD (owner) ======================
@login_required
def download_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id, owner=request.user)
    return _do_download(request, file_obj)


# ====================== DOWNLOAD SHARED ======================
@login_required
def download_shared_file(request, file_id):
    share = get_object_or_404(FileShare, file_id=file_id, shared_with=request.user, can_download=True)

    # ── Check expiry ──
    if share.is_expired():
        messages.error(request, "This share link has expired. The owner would need to share it again.")
        return redirect('shared_with_me')

    return _do_download(request, share.file)


def _do_download(request, file_obj):
    try:
        # Fetch encrypted bytes from IPFS or local
        if file_obj.ipfs_cid:
            try:
                encrypted_data = download_from_ipfs(file_obj.ipfs_cid)
            except Exception as ipfs_err:
                if file_obj.encrypted_file_path and os.path.exists(file_obj.encrypted_file_path):
                    with open(file_obj.encrypted_file_path, 'rb') as f:
                        encrypted_data = f.read()
                else:
                    raise ConnectionError(f"Could not retrieve file from IPFS: {ipfs_err}")
        elif file_obj.encrypted_file_path and os.path.exists(file_obj.encrypted_file_path):
            with open(file_obj.encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
        else:
            raise FileNotFoundError("File not found in IPFS or local storage.")

        # Decrypt
        key_bytes = bytes(file_obj.encryption_key)
        decrypted = decrypt_file(encrypted_data, key_bytes)

        # ── Increment download count ──
        File.objects.filter(pk=file_obj.pk).update(
            download_count=file_obj.download_count + 1
        )

        ActivityLog.objects.create(
            user=request.user, action='download', file_hash=file_obj.file_hash,
            success=True, ip_address=get_client_ip(request),
            details=f"Downloaded: {file_obj.filename}",
        )

        response = HttpResponse(decrypted, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_obj.original_filename}"'
        return response

    except FileNotFoundError as e:
        messages.error(request, f"File not found: {e}")
    except ConnectionError as e:
        messages.error(request, f"Could not retrieve file: {e}")
    except Exception as e:
        messages.error(request, f"Download error: {str(e)}")

    ActivityLog.objects.create(
        user=request.user, action='download', file_hash=file_obj.file_hash,
        success=False, ip_address=get_client_ip(request),
        details=f"Download failed: {file_obj.filename}",
    )
    return redirect('dashboard')


# ====================== DELETE ======================
@login_required
def delete_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id, owner=request.user)
    if request.method != 'POST':
        return redirect('dashboard')

    file_hash = file_obj.file_hash
    filename  = file_obj.filename

    if file_obj.ipfs_cid:
        unpin_from_ipfs(file_obj.ipfs_cid)
    if file_obj.encrypted_file_path and os.path.exists(file_obj.encrypted_file_path):
        os.remove(file_obj.encrypted_file_path)

    file_obj.delete()

    ActivityLog.objects.create(
        user=request.user, action='delete', file_hash=file_hash,
        success=True, ip_address=get_client_ip(request),
        details=f"Deleted: {filename}",
    )
    messages.success(request, f"'{filename}' deleted successfully.")
    return redirect('my_files')


# ====================== MY FILES ======================
@login_required
def my_files(request):
    files = File.objects.filter(owner=request.user).order_by('-upload_date')
    return render(request, 'files/my_files.html', {'files': files})


# ====================== SHARE A FILE ======================
@login_required
def share_file(request, file_id):
    file_obj       = get_object_or_404(File, id=file_id, owner=request.user)
    current_shares = FileShare.objects.filter(file=file_obj).select_related('shared_with')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'revoke':
            share = get_object_or_404(FileShare, id=request.POST.get('share_id'), file=file_obj)
            uname = share.shared_with.username
            share.delete()
            messages.success(request, f"Access revoked for {uname}.")
            return redirect('share_file', file_id=file_id)

        username = request.POST.get('username', '').strip()
        if not username:
            messages.error(request, "Please enter a username.")
        elif username == request.user.username:
            messages.error(request, "You cannot share a file with yourself.")
        else:
            try:
                target = CustomUser.objects.get(username=username)

                # ── Parse expiry date ──
                expiry_days = request.POST.get('expiry_days', '').strip()
                expires_at  = None
                if expiry_days and expiry_days != '0':
                    try:
                        days       = int(expiry_days)
                        expires_at = timezone.now() + datetime.timedelta(days=days)
                    except ValueError:
                        pass

                share, created = FileShare.objects.get_or_create(
                    file=file_obj,
                    shared_with=target,
                    defaults={
                        'shared_by':  request.user,
                        'expires_at': expires_at,
                    },
                )

                if not created:
                    # Update the expiry on an existing share
                    share.expires_at = expires_at
                    share.save(update_fields=['expires_at'])
                    messages.info(request, f"Expiry date updated for {username}.")
                else:
                    # Also call grantAccess on blockchain if both users have wallets
                    if request.user.wallet_address and target.wallet_address:
                        try:
                            w3, contract = get_contract()
                            expiry_ts    = int(expires_at.timestamp()) if expires_at else int(
                                (timezone.now() + datetime.timedelta(days=365)).timestamp()
                            )
                            tx = contract.functions.grantAccess(
                                file_obj.file_hash,
                                target.wallet_address,
                                expiry_ts,
                            ).build_transaction({
                                'from':  request.user.wallet_address,
                                'nonce': w3.eth.get_transaction_count(request.user.wallet_address),
                                'gas':   200000,
                            })
                            tx_hash = w3.eth.send_transaction(tx)
                            w3.eth.wait_for_transaction_receipt(tx_hash)
                        except Exception:
                            pass

                    ActivityLog.objects.create(
                        user=request.user, action='share', file_hash=file_obj.file_hash,
                        success=True, ip_address=get_client_ip(request),
                        details=f"Shared '{file_obj.filename}' with {username}"
                                + (f" (expires {expires_at.strftime('%d %b %Y')})" if expires_at else ""),
                    )

                    expiry_msg = f" — expires in {expiry_days} days" if expiry_days and expiry_days != '0' else " — no expiry"
                    messages.success(request, f"✅ File shared with {username}{expiry_msg}!")

            except CustomUser.DoesNotExist:
                messages.error(request, f"No user found with username '{username}'.")

        return redirect('share_file', file_id=file_id)

    expiry_options = [
        ('0',   'No Expiry'),
        ('1',   '1 Day'),
        ('3',   '3 Days'),
        ('7',   '7 Days'),
        ('14',  '14 Days'),
        ('30',  '1 Month'),
        ('90',  '3 Months'),
        ('180', '6 Months'),
        ('365', '1 Year'),
    ]
    return render(request, 'files/share_file.html', {
        'file':           file_obj,
        'current_shares': current_shares,
        'expiry_options': expiry_options,
    })


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
    result    = None
    query     = ''
    file_hash = ''

    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
    else:
        query = request.GET.get('hash', '').strip()

    if query:
        is_hash = len(query) == 64 and all(c in '0123456789abcdefABCDEF' for c in query)

        if is_hash:
            file_hash = query.lower()
            try:
                db_file = File.objects.get(file_hash=file_hash)
            except File.DoesNotExist:
                db_file = None
        else:
            db_results = File.objects.filter(filename__icontains=query, owner=request.user).order_by('-upload_date')
            if db_results.count() == 1:
                db_file   = db_results.first()
                file_hash = db_file.file_hash
            elif db_results.count() > 1:
                return render(request, 'blockchain/verify.html', {
                    'multiple_results': db_results,
                    'query':            query,
                    'my_files': File.objects.filter(owner=request.user).order_by('-upload_date'),
                })
            else:
                db_file = None

        blockchain_data  = None
        blockchain_error = None

        if file_hash:
            try:
                w3, contract   = get_contract()
                chain_file     = contract.functions.files(file_hash).call()
                stored_hash    = chain_file[0]
                owner_wallet   = chain_file[1]
                upload_time_ts = chain_file[2]
                is_active      = chain_file[3]

                if stored_hash and upload_time_ts > 0:
                    blockchain_data = {
                        'file_hash':    stored_hash,
                        'owner_wallet': owner_wallet,
                        'upload_time':  datetime.datetime.fromtimestamp(upload_time_ts),
                        'is_active':    is_active,
                    }
                else:
                    blockchain_error = (
                        "Hash not found on blockchain. Ganache may have been restarted. "
                        "Run python redeploy_contract.py then re-upload the file."
                    )
            except ConnectionError:
                blockchain_error = "Cannot connect to Ganache. Make sure it is running."
            except Exception as e:
                blockchain_error = str(e)

        result = {
            'query':            query,
            'file_hash':        file_hash,
            'db_file':          db_file,
            'blockchain_data':  blockchain_data,
            'blockchain_error': blockchain_error,
            'verified': blockchain_data is not None and blockchain_data.get('is_active', False),
        }

    my_files_qs = File.objects.filter(owner=request.user).order_by('-upload_date')
    return render(request, 'blockchain/verify.html', {
        'result':   result,
        'query':    query,
        'my_files': my_files_qs,
    })
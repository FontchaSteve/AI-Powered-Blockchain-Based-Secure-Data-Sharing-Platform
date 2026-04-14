from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
import os

from .forms import FileUploadForm
from .encryption_utils import generate_file_hash, encrypt_file, save_encrypted_file, decrypt_file
from .models import File
from blockchain.contract_interaction import get_contract
from users.models import ActivityLog


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ====================== DASHBOARD ======================
@login_required
def dashboard(request):
    recent_files = File.objects.filter(owner=request.user).order_by('-upload_date')[:6]
    total_files = File.objects.filter(owner=request.user).count()
    recent_activity = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:10]

    context = {
        'recent_files': recent_files,
        'total_files': total_files,
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

            # Step 1: Hash
            file_hash = generate_file_hash(file_data)

            # Step 2: Check for duplicate
            if File.objects.filter(file_hash=file_hash).exists():
                messages.warning(request, "This file already exists in your vault.")
                return redirect('my_files')

            # Step 3: Encrypt
            encrypted_data, encryption_key = encrypt_file(file_data)

            # Step 4: Save to disk
            encrypted_filename = f"enc_{file_hash[:16]}_{uploaded_file.name}"
            file_path = save_encrypted_file(encrypted_data, encrypted_filename)

            # Step 5: Register on blockchain
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
                # Blockchain failed — save file anyway with no tx hash
                tx_hash_hex = None
                messages.warning(
                    request,
                    f"File encrypted and saved, but blockchain registration failed: {str(e)}"
                )

            # Step 6: Save to DB
            File.objects.create(
                owner=request.user,
                filename=uploaded_file.name,
                original_filename=uploaded_file.name,
                file_hash=file_hash,
                encrypted_file_path=file_path,
                encryption_key=encryption_key,
                blockchain_tx_hash=tx_hash_hex,
            )

            # Step 7: Log for AI
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


# ====================== DOWNLOAD ======================
@login_required
def download_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id, owner=request.user)

    try:
        with open(file_obj.encrypted_file_path, 'rb') as f:
            encrypted_data = f.read()

        # ← FIXED: BinaryField returns memoryview — must convert to bytes first
        key_bytes = bytes(file_obj.encryption_key)
        decrypted_data = decrypt_file(encrypted_data, key_bytes)

        ActivityLog.objects.create(
            user=request.user,
            action='download',
            file_hash=file_obj.file_hash,
            success=True,
            ip_address=get_client_ip(request),
            details=f"File downloaded: {file_obj.filename}",
        )

        response = HttpResponse(decrypted_data, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_obj.original_filename}"'
        return response

    except FileNotFoundError:
        messages.error(request, "Encrypted file not found on disk. It may have been moved or deleted.")
        ActivityLog.objects.create(
            user=request.user,
            action='download',
            file_hash=file_obj.file_hash,
            success=False,
            ip_address=get_client_ip(request),
            details=f"Download failed — file not found on disk: {file_obj.filename}",
        )
        return redirect('dashboard')

    except Exception as e:
        messages.error(request, f"Download error: {str(e)}")
        ActivityLog.objects.create(
            user=request.user,
            action='download',
            file_hash=file_obj.file_hash,
            success=False,
            ip_address=get_client_ip(request),
            details=f"Download error: {str(e)}",
        )
        return redirect('dashboard')


# ====================== DELETE ======================
@login_required
def delete_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id, owner=request.user)

    # Only allow POST for destructive actions (GET-based deletes are unsafe)
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('dashboard')

    file_hash = file_obj.file_hash
    filename = file_obj.filename

    # Remove from disk
    if os.path.exists(file_obj.encrypted_file_path):
        os.remove(file_obj.encrypted_file_path)

    # Remove from DB
    file_obj.delete()

    ActivityLog.objects.create(
        user=request.user,
        action='delete',
        file_hash=file_hash,
        success=True,
        ip_address=get_client_ip(request),
        details=f"File deleted: {filename}",
    )

    messages.success(request, f"File '{filename}' deleted successfully.")
    return redirect('dashboard')


# ====================== MY FILES ======================
@login_required
def my_files(request):
    files = File.objects.filter(owner=request.user).order_by('-upload_date')
    return render(request, 'files/my_files.html', {'files': files})
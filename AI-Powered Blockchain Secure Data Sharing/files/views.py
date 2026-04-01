from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import FileUploadForm
from .encryption_utils import generate_file_hash, encrypt_file, save_encrypted_file
from .models import File
from blockchain.contract_interaction import get_contract
from users.models import ActivityLog

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            file_data = uploaded_file.read()

            # Step 1: Generate hash
            file_hash = generate_file_hash(file_data)

            # Step 2: Encrypt file
            encrypted_data, encryption_key = encrypt_file(file_data)

            # Step 3: Save encrypted file locally
            encrypted_filename = f"enc_{file_hash[:16]}_{uploaded_file.name}"
            file_path = save_encrypted_file(encrypted_data, encrypted_filename)

            # Step 4: Register on Blockchain
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

                messages.success(request, f"✅ File uploaded successfully! Tx: {tx_hash.hex()[:10]}...")

                # Save to database
                new_file = File.objects.create(
                    owner=request.user,
                    filename=uploaded_file.name,
                    original_filename=uploaded_file.name,
                    file_hash=file_hash,
                    encrypted_file_path=file_path,
                    blockchain_tx_hash=tx_hash.hex()
                )

                # Log for AI
                ActivityLog.objects.create(
                    user=request.user,
                    action='upload',
                    file_hash=file_hash,
                    success=True,
                    details=f"File uploaded: {uploaded_file.name}"
                )

                return redirect('my_files')

            except Exception as e:
                messages.error(request, f"Blockchain error: {str(e)}")
                return redirect('upload_file')

    else:
        form = FileUploadForm()

    return render(request, 'files/upload.html', {'form': form})


@login_required
def my_files(request):
    files = File.objects.filter(owner=request.user).order_by('-upload_date')
    return render(request, 'files/my_files.html', {'files': files})
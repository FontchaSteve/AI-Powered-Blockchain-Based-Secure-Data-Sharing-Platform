from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import os
from django.conf import settings

def generate_file_hash(file_data):
    """Generate SHA-256 hash of the original file"""
    sha256 = hashlib.sha256()
    sha256.update(file_data)
    return sha256.hexdigest()

def encrypt_file(file_data, key=None):
    """Encrypt file using AES-256"""
    if key is None:
        key = os.urandom(32)  # Generate random 256-bit key
    
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(file_data, AES.block_size))
    
    # Return encrypted data + IV
    return cipher.iv + ct_bytes, key

def decrypt_file(encrypted_data, key):
    """Decrypt file (we may need this later)"""
    iv = encrypted_data[:16]
    ct = encrypted_data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)

def save_encrypted_file(encrypted_data, filename):
    """Save encrypted file to media/files/ folder"""
    file_path = os.path.join(settings.MEDIA_ROOT, 'files', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'wb') as f:
        f.write(encrypted_data)
    
    return file_path
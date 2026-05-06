"""
Email notification utilities for SecureShare.
Sends a beautiful HTML email when a file is shared with a user.
"""

import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


def get_file_icon(filename):
    """Return an emoji icon based on file extension."""
    n = filename.lower()
    if '.pdf'  in n: return '📕'
    if any(e in n for e in ['.png', '.jpg', '.jpeg', '.gif', '.webp']): return '🖼️'
    if any(e in n for e in ['.mp4', '.avi', '.mov', '.mkv']): return '🎬'
    if any(e in n for e in ['.doc', '.docx']): return '📝'
    if any(e in n for e in ['.xls', '.xlsx', '.csv']): return '📊'
    if any(e in n for e in ['.zip', '.rar', '.7z']): return '📦'
    if any(e in n for e in ['.mp3', '.wav', '.aac']): return '🎵'
    if any(e in n for e in ['.py', '.js', '.html', '.css', '.json']): return '💻'
    return '📄'


def send_file_shared_email(share):
    """
    Send a notification email to the recipient of a file share.

    Args:
        share: FileShare instance (with .file, .shared_by, .shared_with, .expires_at)
    """
    recipient = share.shared_with
    sender    = share.shared_by
    file_obj  = share.file

    # Only send if recipient has a real email
    if not recipient.email:
        return False

    # Only send if email is configured in settings
    if not getattr(settings, 'EMAIL_HOST_USER', ''):
        print("[SecureShare] Email not configured — skipping notification.")
        return False

    # Build expiry display text
    expires_at_formatted = None
    expiry_display       = None

    if share.expires_at:
        expires_at_formatted = share.expires_at.strftime('%d %B %Y at %H:%M UTC')
        delta = share.expires_at - timezone.now()
        days  = delta.days
        if days == 0:
            hours = int(delta.seconds / 3600)
            expiry_display = f"{hours} hour{'s' if hours != 1 else ''}"
        elif days == 1:
            expiry_display = "1 day"
        elif days < 30:
            expiry_display = f"{days} days"
        elif days < 60:
            expiry_display = "1 month"
        elif days < 365:
            months = round(days / 30)
            expiry_display = f"{months} months"
        else:
            expiry_display = "1 year"

    # Build the login URL
    login_url = f"http://127.0.0.1:8000/accounts/login/"

    context = {
        'recipient_name':      recipient.username,
        'sender_name':         sender.username,
        'file_name':           file_obj.filename,
        'file_icon':           get_file_icon(file_obj.filename),
        'file_size':           file_obj.file_size_display,
        'storage_mode':        file_obj.storage_mode,
        'blockchain_verified': bool(file_obj.blockchain_tx_hash),
        'expires_at':          share.expires_at,
        'expires_at_formatted':expires_at_formatted,
        'expiry_display':      expiry_display,
        'shared_at':           share.shared_at.strftime('%d %B %Y'),
        'login_url':           login_url,
    }

    # Render the HTML email
    html_content = render_to_string('emails/file_shared.html', context)

    # Plain text fallback
    if share.expires_at:
        expiry_text = f"You have {expiry_display} to access this file (expires {expires_at_formatted})."
    else:
        expiry_text = "This file has been shared with you permanently — no expiry date."

    text_content = f"""
Hello {recipient.username},

{sender.username} has shared an encrypted file with you on SecureShare.

File: {file_obj.filename}
Size: {file_obj.file_size_display}

{expiry_text}

Log in to access your files: {login_url}

This file is AES-256 encrypted and secured on the blockchain.

— The SecureShare Team
    """.strip()

    # Build and send email
    subject = f"📁 {sender.username} shared a file with you — SecureShare"

    try:
        msg = EmailMultiAlternatives(
            subject      = subject,
            body         = text_content,
            from_email   = settings.DEFAULT_FROM_EMAIL,
            to           = [recipient.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        print(f"[SecureShare] Email sent to {recipient.email}")
        return True

    except Exception as e:
        print(f"[SecureShare] Email failed: {e}")
        return False
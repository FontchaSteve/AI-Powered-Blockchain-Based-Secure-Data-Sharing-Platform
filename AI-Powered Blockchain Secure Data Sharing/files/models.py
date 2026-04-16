from django.db import models
from users.models import CustomUser
from django.utils import timezone


class File(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_files')
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=128, unique=True)
    encrypted_file_path = models.CharField(max_length=500)
    encryption_key = models.BinaryField()
    blockchain_tx_hash = models.CharField(max_length=66, blank=True, null=True)
    upload_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.filename} - {self.owner.username}"


class FileShare(models.Model):
    """Tracks which files have been shared with which users."""
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shares_given')
    shared_with = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shares_received')
    shared_at = models.DateTimeField(default=timezone.now)
    # Optional: expiry date — leave null = never expires
    expires_at = models.DateTimeField(null=True, blank=True)
    can_download = models.BooleanField(default=True)

    class Meta:
        # A user can only be shared a specific file once
        unique_together = ('file', 'shared_with')
        ordering = ['-shared_at']

    def is_expired(self):
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.file.filename} → {self.shared_with.username}"
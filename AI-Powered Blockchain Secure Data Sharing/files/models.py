from django.db import models
from users.models import CustomUser
from django.utils import timezone


class File(models.Model):
    owner               = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_files')
    filename            = models.CharField(max_length=255)
    original_filename   = models.CharField(max_length=255)
    file_hash           = models.CharField(max_length=128, unique=True)
    encrypted_file_path = models.CharField(max_length=500, blank=True)
    ipfs_cid            = models.CharField(max_length=100, blank=True, null=True)
    encryption_key      = models.BinaryField()
    blockchain_tx_hash  = models.CharField(max_length=66, blank=True, null=True)
    upload_date         = models.DateTimeField(default=timezone.now)
    file_size           = models.PositiveBigIntegerField(default=0)
    download_count      = models.PositiveIntegerField(default=0)
    is_active           = models.BooleanField(default=True)

    @property
    def storage_mode(self):
        return 'ipfs' if self.ipfs_cid else 'local'

    @property
    def file_size_display(self):
        size = self.file_size
        if size == 0:
            return '—'
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def __str__(self):
        return f"{self.filename} - {self.owner.username}"


class FileShare(models.Model):
    file         = models.ForeignKey(File, on_delete=models.CASCADE, related_name='shares')
    shared_by    = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shares_given')
    shared_with  = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shares_received')
    shared_at    = models.DateTimeField(default=timezone.now)
    expires_at   = models.DateTimeField(null=True, blank=True)
    can_download = models.BooleanField(default=True)

    class Meta:
        unique_together = ('file', 'shared_with')
        ordering = ['-shared_at']

    def is_expired(self):
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @property
    def expiry_display(self):
        if self.expires_at is None:
            return 'Never expires'
        if self.is_expired():
            return 'Expired'
        delta = self.expires_at - timezone.now()
        days  = delta.days
        if days == 0:
            hours = int(delta.seconds / 3600)
            return f'Expires in {hours}h'
        return f'Expires in {days} day{"s" if days != 1 else ""}'

    def __str__(self):
        return f"{self.file.filename} → {self.shared_with.username}"
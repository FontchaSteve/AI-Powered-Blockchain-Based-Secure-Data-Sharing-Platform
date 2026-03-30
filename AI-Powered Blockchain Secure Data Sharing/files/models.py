from django.db import models
from users.models import CustomUser
from django.utils import timezone

class File(models.Model):
    """Main File model - stores metadata"""
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=255, unique=True)   # SHA256 or IPFS hash
    encrypted_file_path = models.CharField(max_length=500)      # Local path to encrypted file
    upload_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.filename} ({self.owner.username})"


class AccessPermission(models.Model):
    """Access control for files"""
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='permissions')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    granted_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='granted_permissions')
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)
    expiration_date = models.DateTimeField(null=True, blank=True)
    granted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('file', 'user')

    def __str__(self):
        return f"{self.user.username} access to {self.file.filename}"
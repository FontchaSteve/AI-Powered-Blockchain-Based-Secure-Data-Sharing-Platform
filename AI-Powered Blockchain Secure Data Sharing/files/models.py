from django.db import models
from users.models import CustomUser
from django.utils import timezone

class File(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_files')
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=128, unique=True)        # SHA-256 hash
    encrypted_file_path = models.CharField(max_length=500)
    blockchain_tx_hash = models.CharField(max_length=66, blank=True, null=True)  # Transaction hash from blockchain
    upload_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.filename} - {self.owner.username}"
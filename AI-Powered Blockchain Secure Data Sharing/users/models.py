from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    """Custom User Model"""
    email = models.EmailField(unique=True)
    wallet_address = models.CharField(max_length=42, blank=True, null=True)

    def __str__(self):
        return self.username


class ActivityLog(models.Model):
    """Activity logs for AI anomaly detection"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,      # ← FIXED: allows logging failed logins with no user
        blank=True,
    )
    action = models.CharField(max_length=50)  # 'login', 'upload', 'download', 'delete', 'failed_login'
    file_hash = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    success = models.BooleanField(default=True)
    details = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} - {self.action} at {self.timestamp}"
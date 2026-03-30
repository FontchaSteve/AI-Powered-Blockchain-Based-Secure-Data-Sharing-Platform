from django.db import models
from users.models import CustomUser
from django.utils import timezone

class AnomalyAlert(models.Model):
    """AI detected anomalies"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    alert_type = models.CharField(max_length=100)   # e.g., 'suspicious_login', 'unusual_access'
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    detected_at = models.DateTimeField(default=timezone.now)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.alert_type} - {self.severity}"
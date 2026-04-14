from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import ActivityLog
from .anomaly_detector import detect_anomalies

# Map model severity levels → Bootstrap alert classes
SEVERITY_TO_BOOTSTRAP = {
    'high':   'danger',
    'medium': 'warning',
    'low':    'info',
    'info':   'info',
}


@login_required
def ai_monitor(request):
    user_logs = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:50]

    raw_anomalies = detect_anomalies()

    # Attach the correct Bootstrap colour class to each anomaly
    anomalies = []
    for anomaly in raw_anomalies:
        severity = anomaly.get('severity', 'medium')
        anomaly['bootstrap_class'] = SEVERITY_TO_BOOTSTRAP.get(severity, 'warning')
        anomalies.append(anomaly)

    context = {
        'user_logs': user_logs,
        'anomalies': anomalies,
        'total_uploads': ActivityLog.objects.filter(action='upload').count(),
        'total_access': ActivityLog.objects.filter(action__in=['access', 'download']).count(),
        'total_failed_logins': ActivityLog.objects.filter(action='failed_login').count(),
    }

    return render(request, 'ai_monitor/dashboard.html', context)
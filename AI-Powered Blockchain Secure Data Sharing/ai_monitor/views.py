from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import ActivityLog
from .anomaly_detector import detect_anomalies

SEVERITY_TO_BOOTSTRAP = {
    'high':   'danger',
    'medium': 'warning',
    'low':    'info',
    'info':   'info',
}


@login_required
def ai_monitor(request):
    # ✅ FIXED: all queries filtered to current user only
    user_logs = ActivityLog.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:50]

    # Anomalies scoped to this user
    raw_anomalies = detect_anomalies(user=request.user)

    anomalies = []
    for anomaly in raw_anomalies:
        severity = anomaly.get('severity', 'medium')
        anomaly['bootstrap_class'] = SEVERITY_TO_BOOTSTRAP.get(severity, 'warning')
        anomalies.append(anomaly)

    context = {
        'user_logs':           user_logs,
        'anomalies':           anomalies,
        # ✅ FIXED: filtered by current user — not system-wide counts
        'total_uploads':       ActivityLog.objects.filter(user=request.user, action='upload').count(),
        'total_downloads':     ActivityLog.objects.filter(user=request.user, action='download').count(),
        'total_failed_logins': ActivityLog.objects.filter(user=request.user, action='failed_login').count(),
        'total_anomalies':     len(anomalies),
    }

    return render(request, 'ai_monitor/dashboard.html', context)
import pandas as pd
from sklearn.ensemble import IsolationForest
from users.models import ActivityLog
from django.utils import timezone
from datetime import timedelta


def detect_anomalies(user=None):
    """
    AI Anomaly Detection — scoped to a single user.
    Pass user=request.user so each account only sees its own alerts.
    """
    # ✅ FIXED: filter to current user's logs only
    qs = ActivityLog.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=30)
    )
    if user is not None:
        qs = qs.filter(user=user)

    logs = qs.order_by('timestamp')

    if len(logs) < 10:
        return [{
            'type': 'info',
            'description': 'Not enough data yet. Keep using the platform — AI analysis activates after 10 events.',
            'severity': 'low',
        }]

    data = []
    for log in logs:
        # ✅ FIXED: user can be None for failed_login rows — guard gracefully
        uid      = log.user.id       if log.user else 0
        uname    = log.user.username if log.user else 'Anonymous'

        data.append({
            'user_id':     uid,
            'username':    uname,
            'action':      log.action,
            'hour':        log.timestamp.hour,
            'day_of_week': log.timestamp.weekday(),
            'success':     1 if log.success else 0,
            'timestamp':   log.timestamp,
        })

    df = pd.DataFrame(data)
    if df.empty:
        return []

    features = pd.get_dummies(df[['action', 'hour', 'day_of_week']], drop_first=True)
    features['success'] = df['success']

    model = IsolationForest(contamination=0.15, random_state=42, n_estimators=100)
    df['anomaly_score'] = model.fit_predict(features)

    anomalies_df = df[df['anomaly_score'] == -1]

    alert_list = []

    if len(anomalies_df) > 5:
        alert_list.insert(0, {
            'type':        'warning',
            'description': 'High number of suspicious activities detected in the last 30 days.',
            'severity':    'high',
        })

    for _, row in anomalies_df.iterrows():
        severity = 'high' if row['success'] == 0 else 'medium'
        alert_list.append({
            'type':        'suspicious_activity',
            'description': f"Suspicious {row['action']} activity detected",
            'severity':    severity,
            'time':        row['timestamp'].strftime('%d %b %H:%M'),
            'user_id':     row['user_id'],
        })

    return alert_list
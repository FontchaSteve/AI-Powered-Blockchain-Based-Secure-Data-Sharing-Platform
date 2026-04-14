import pandas as pd
from sklearn.ensemble import IsolationForest
from users.models import ActivityLog
from django.utils import timezone
from datetime import timedelta

def detect_anomalies():
    """Enhanced AI Anomaly Detection"""
    
    # Get last 30 days of logs
    logs = ActivityLog.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).order_by('timestamp')
    
    if len(logs) < 10:
        return [{
            'type': 'info',
            'description': 'Not enough data to run AI analysis yet. Continue using the platform.',
            'severity': 'low'
        }]

    data = []
    for log in logs:
        # ← FIXED: user can be None for failed_login events — handle gracefully
        user_id = log.user.id if log.user else 0
        username = log.user.username if log.user else 'Anonymous'

        data.append({
            'user_id': user_id,
            'username': username,
            'action': log.action,
            'hour': log.timestamp.hour,
            'day_of_week': log.timestamp.weekday(),
            'success': 1 if log.success else 0,
            'timestamp': log.timestamp,
        })

    df = pd.DataFrame(data)
    
    if df.empty:
        return []

    # Feature engineering
    features = pd.get_dummies(df[['action', 'hour', 'day_of_week']], drop_first=True)
    features['success'] = df['success']

    # Train Isolation Forest
    model = IsolationForest(contamination=0.15, random_state=42, n_estimators=100)
    df['anomaly_score'] = model.fit_predict(features)

    # Get anomalies
    anomalies_df = df[df['anomaly_score'] == -1]

    alert_list = []
    for _, row in anomalies_df.iterrows():
        severity = 'high' if row['success'] == 0 else 'medium'
        
        alert_list.append({
            'type': 'suspicious_activity',
            'description': f"Suspicious {row['action']} activity detected for user {row['username']}",
            'severity': severity,
            'time': row['timestamp'].strftime("%d %b %H:%M"),
            'user_id': row['user_id']
        })

    # Add system-level insights
    if len(anomalies_df) > 5:
        alert_list.insert(0, {
            'type': 'warning',
            'description': 'High number of suspicious activities detected in the last 30 days.',
            'severity': 'high'
        })

    return alert_list
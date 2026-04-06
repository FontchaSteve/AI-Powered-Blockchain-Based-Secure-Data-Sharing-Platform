import pandas as pd
from sklearn.ensemble import IsolationForest
from users.models import ActivityLog
from django.utils import timezone
from datetime import timedelta

def detect_anomalies():
    """Detect suspicious activity using Isolation Forest"""
    
    # Get recent activity logs (last 7 days)
    logs = ActivityLog.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=7)
    ).order_by('timestamp')
    
    if len(logs) < 5:
        return []  # Not enough data to detect anomalies
    
    # Convert to DataFrame for analysis
    data = []
    for log in logs:
        data.append({
            'user_id': log.user.id,
            'action': log.action,
            'hour': log.timestamp.hour,
            'day_of_week': log.timestamp.weekday(),
            'success': 1 if log.success else 0,
        })
    
    df = pd.DataFrame(data)
    
    if df.empty:
        return []
    
    # Feature engineering
    features = pd.get_dummies(df[['action', 'hour', 'day_of_week']], drop_first=True)
    features['success'] = df['success']
    
    # Train Isolation Forest (unsupervised anomaly detection)
    model = IsolationForest(contamination=0.1, random_state=42)
    df['anomaly_score'] = model.fit_predict(features)
    
    # Get anomalies (where score == -1)
    anomalies = df[df['anomaly_score'] == -1]
    
    alert_list = []
    for _, row in anomalies.iterrows():
        alert_list.append({
            'type': 'suspicious_activity',
            'description': f"Suspicious {row['action']} activity detected",
            'severity': 'high' if row['success'] == 0 else 'medium',
            'user_id': row['user_id']
        })
    
    return alert_list
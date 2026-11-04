"""
Alert generation and detection service.
Monitors for complaint spikes and SLA breaches.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from app.services.geocoder import get_geo_service

class AlertService:
    def __init__(self, threshold_count: int = 5, window_hours: int = 24):
        self.threshold_count = threshold_count
        self.window_hours = window_hours
        self.geo_service = get_geo_service()

    def detect_spikes(self, complaints: List[Dict]) -> List[Dict]:
        """
        Detect complaint spikes by category and location.

        Returns:
            List of alert dicts with spike details
        """
        # Filter recent complaints
        cutoff_time = datetime.utcnow() - timedelta(hours=self.window_hours)
        recent = [
            c for c in complaints
            if c.get('created_at', datetime.utcnow()) >= cutoff_time
        ]

        # Detect spatial clusters
        clusters = self.geo_service.detect_spatial_spike(
            recent,
            threshold=self.threshold_count,
            window_hours=self.window_hours
        )

        alerts = []
        for cluster in clusters:
            alerts.append({
                'alert_type': 'spike',
                'category': cluster['category'],
                'latitude': cluster['center_lat'],
                'longitude': cluster['center_lon'],
                'complaint_count': cluster['count'],
                'severity': 'high' if cluster['count'] >= self.threshold_count * 2 else 'medium',
                'title': f"{cluster['category'].capitalize()} spike detected",
                'description': f"{cluster['count']} {cluster['category']} complaints in the same area within {self.window_hours} hours"
            })

        return alerts

    def check_sla_breaches(self, issues: List[Dict], sla_hours: int = 48) -> List[Dict]:
        """
        Check for SLA breaches on open issues.

        Args:
            issues: List of issue dicts
            sla_hours: SLA threshold in hours

        Returns:
            List of alert dicts for breached issues
        """
        alerts = []
        now = datetime.utcnow()
        sla_threshold = timedelta(hours=sla_hours)

        for issue in issues:
            if issue.get('status') in ['resolved', 'closed']:
                continue

            created_at = issue.get('created_at', now)
            time_elapsed = now - created_at

            if time_elapsed >= sla_threshold:
                hours_elapsed = int(time_elapsed.total_seconds() / 3600)

                alerts.append({
                    'alert_type': 'sla_breach',
                    'category': issue.get('category', 'unknown'),
                    'issue_id': issue.get('issue_id'),
                    'severity': 'critical',
                    'title': f"SLA breach: Issue {issue.get('issue_id')}",
                    'description': f"Issue open for {hours_elapsed} hours (SLA: {sla_hours}h)"
                })

        return alerts

    def generate_alerts(self, complaints: List[Dict], issues: List[Dict]) -> List[Dict]:
        """
        Generate all types of alerts.

        Returns:
            Combined list of alerts
        """
        alerts = []

        # Spike detection
        spike_alerts = self.detect_spikes(complaints)
        alerts.extend(spike_alerts)

        # SLA breach detection
        sla_alerts = self.check_sla_breaches(issues)
        alerts.extend(sla_alerts)

        return alerts

# Global instance
_alert_service = None

def get_alert_service(threshold_count: int = 5, window_hours: int = 24) -> AlertService:
    """Get or create global alert service instance."""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService(threshold_count, window_hours)
    return _alert_service

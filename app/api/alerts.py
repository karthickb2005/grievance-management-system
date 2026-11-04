"""
Alert detection and retrieval endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Alert, Complaint, Issue, Ward
from app.services.alerting import get_alert_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

class AlertResponse(BaseModel):
    id: int
    alert_id: str
    alert_type: str
    category: Optional[str]
    ward_number: Optional[int]
    ward_name: Optional[str]
    complaint_count: int
    severity: str
    title: str
    description: str
    acknowledged: bool
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AlertResponse])
def list_alerts(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    List alerts.

    Args:
        active_only: Only show unresolved alerts
    """
    query = db.query(Alert)

    if active_only:
        query = query.filter_by(resolved=0)

    alerts = query.order_by(Alert.created_at.desc()).all()

    results = []
    for alert in alerts:
        ward_num = alert.ward.ward_number if alert.ward else None
        ward_name = alert.ward.name if alert.ward else None

        results.append(AlertResponse(
            id=alert.id,
            alert_id=alert.alert_id,
            alert_type=alert.alert_type,
            category=alert.category,
            ward_number=ward_num,
            ward_name=ward_name,
            complaint_count=alert.complaint_count,
            severity=alert.severity.value,
            title=alert.title,
            description=alert.description,
            acknowledged=bool(alert.acknowledged),
            resolved=bool(alert.resolved),
            created_at=alert.created_at
        ))

    return results

@router.post("/generate")
def generate_alerts(db: Session = Depends(get_db)):
    """
    Manually trigger alert generation.

    Checks for spikes and SLA breaches.
    """
    alert_service = get_alert_service()

    # Get recent complaints
    complaints = db.query(Complaint).all()
    complaint_dicts = [{
        'id': c.id,
        'category': c.category,
        'latitude': c.latitude,
        'longitude': c.longitude,
        'created_at': c.created_at
    } for c in complaints]

    # Get open issues
    issues = db.query(Issue).filter_by(status='submitted').all()
    issue_dicts = [{
        'id': i.id,
        'issue_id': i.issue_id,
        'category': i.category,
        'status': i.status.value,
        'created_at': i.created_at
    } for i in issues]

    # Generate alerts
    new_alerts = alert_service.generate_alerts(complaint_dicts, issue_dicts)

    created_count = 0
    for alert_data in new_alerts:
        # Check if alert already exists
        existing = db.query(Alert).filter_by(
            alert_type=alert_data['alert_type'],
            category=alert_data['category']
        ).filter(Alert.resolved == 0).first()

        if not existing:
            # Find ward if location provided
            ward = None
            if 'latitude' in alert_data and 'longitude' in alert_data:
                # Find nearest ward (simplified)
                wards = db.query(Ward).all()
                if wards:
                    from app.services.geocoder import get_geo_service
                    geo_service = get_geo_service()

                    min_dist = float('inf')
                    for w in wards:
                        dist = geo_service.distance_meters(
                            alert_data['latitude'], alert_data['longitude'],
                            w.center_lat, w.center_lon
                        )
                        if dist < min_dist:
                            min_dist = dist
                            ward = w

            alert_count = db.query(Alert).count() + 1
            alert_id = f"ALR-{alert_count:05d}"

            new_alert = Alert(
                alert_id=alert_id,
                alert_type=alert_data['alert_type'],
                category=alert_data.get('category'),
                ward_id=ward.id if ward else None,
                complaint_count=alert_data.get('complaint_count', 0),
                severity=alert_data['severity'],
                title=alert_data['title'],
                description=alert_data['description'],
                acknowledged=0,
                resolved=0
            )
            db.add(new_alert)
            created_count += 1

    db.commit()

    return {
        "message": f"Generated {created_count} new alerts",
        "total_alerts": len(new_alerts)
    }

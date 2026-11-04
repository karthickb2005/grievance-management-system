"""
Demo burst script - creates a spike scenario in Ward 112 for testing alerts.
"""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Complaint, Issue, Department, Ward, SeverityLevel, ComplaintStatus
from app.services.alerting import get_alert_service

# Ward 112 center (Rajajinagar area)
WARD_112_LAT = 12.9985
WARD_112_LON = 77.5477

# Water-related complaint texts for the spike
WATER_COMPLAINTS = [
    "water pipeline burst, road flooded with water",
    "major water leak, water gushing from pipe",
    "water pipeline broken, street waterlogged",
    "severe water leakage, drinking water wasted",
    "water pipe burst causing flooding",
    "emergency - water pipeline damaged",
    "water supply pipe burst, no water in area",
    "big water leak, road completely filled with water",
    "water drainage problem, pipeline broken",
    "water supply pipe damaged, severe leakage",
]

def create_demo_burst():
    """Create a burst of water complaints in Ward 112."""
    print("=" * 60)
    print("DEMO BURST - Creating Water Spike in Ward 112")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Get Ward 112
        ward = db.query(Ward).filter_by(ward_number=112).first()
        if not ward:
            print("ERROR: Ward 112 not found. Run seed.py first.")
            return

        print(f"\nWard: {ward.name} (Ward {ward.ward_number})")
        print(f"Location: {ward.center_lat}, {ward.center_lon}")

        # Get Water department
        dept = db.query(Department).filter(
            Department.name.like("%Water%")
        ).first()

        if not dept:
            print("ERROR: Water department not found. Run seed.py first.")
            return

        print(f"Department: {dept.name}")

        # Count existing complaints in ward
        existing = db.query(Complaint).filter_by(ward_id=ward.id).count()
        print(f"\nExisting complaints in Ward 112: {existing}")

        # Create burst complaints
        print(f"\nCreating {len(WATER_COMPLAINTS)} water complaints...")

        for i, text in enumerate(WATER_COMPLAINTS):
            # Generate complaint ID
            complaint_num = existing + i + 1
            complaint_id = f"BBMP-2024-W{ward.ward_number:03d}-{complaint_num:05d}"

            # Random location within ~100m of ward center
            lat = ward.center_lat + random.uniform(-0.001, 0.001)
            lon = ward.center_lon + random.uniform(-0.001, 0.001)

            # Create complaint
            complaint = Complaint(
                complaint_id=complaint_id,
                text=text,
                language="en",
                category="water",
                department_id=dept.id,
                severity=random.choice([SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL]),
                latitude=lat,
                longitude=lon,
                ward_id=ward.id,
                citizen_name=f"Citizen {complaint_num}",
                citizen_phone=f"9{random.randint(100000000, 999999999)}",
                status=ComplaintStatus.SUBMITTED,
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 6))
            )
            db.add(complaint)
            print(f"  [{i+1}] {complaint_id}: {text[:40]}...")

        db.commit()

        # Get created complaints
        new_complaints = db.query(Complaint).filter(
            Complaint.ward_id == ward.id,
            Complaint.category == "water",
            Complaint.complaint_id.like(f"BBMP-2024-W{ward.ward_number:03d}%")
        ).order_by(Complaint.id.desc()).limit(10).all()

        print(f"\n✓ Created {len(new_complaints)} water complaints in Ward 112")

        # Generate alert
        print("\nGenerating alert...")

        alert_service = get_alert_service()
        complaint_dicts = [{
            'id': c.id,
            'category': c.category,
            'latitude': c.latitude,
            'longitude': c.longitude,
            'created_at': c.created_at
        } for c in new_complaints]

        spikes = alert_service.detect_spikes(complaint_dicts)

        if spikes:
            print(f"\n✓ SPIKE DETECTED!")
            for spike in spikes:
                print(f"  - Category: {spike['category']}")
                print(f"  - Count: {spike['complaint_count']} complaints")
                print(f"  - Location: {spike['center_lat']:.4f}, {spike['center_lon']:.4f}")
                print(f"  - Severity: {spike['severity']}")
        else:
            print("\n⚠ No spike detected (may need threshold adjustment)")

        print("\n" + "=" * 60)
        print("DEMO BURST COMPLETE")
        print("=" * 60)
        print("\nTo verify:")
        print("  1. Check API: GET /api/alerts")
        print("  2. Check geo: GET /api/geo/hex-density?category=water")
        print("  3. Check Ward 112 complaints in frontend")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_burst()
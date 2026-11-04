"""
Seed data for Grievance Router.
Creates departments and sample BBMP wards.
"""
import os
import sys
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Department, Ward, Complaint, Issue, SeverityLevel, ComplaintStatus

# Sample BBMP wards (subset of 243 wards - using major areas)
BBMP_WARDS = [
    # South Bangalore
    {"ward_number": 150, "name": "HSR Layout", "name_kn": "ಎಚ್.ಎಸ್.ಆರ್ ಬಡಾವಣೆ", "zone": "South", "lat": 12.9121, "lon": 77.6446},
    {"ward_number": 174, "name": "Koramangala", "name_kn": "ಕೋರಮಂಗಲ", "zone": "South", "lat": 12.9352, "lon": 77.6245},
    {"ward_number": 173, "name": "Ejipura", "name_kn": "ಎಜಿಪುರ", "zone": "South", "lat": 12.9466, "lon": 77.6122},
    {"ward_number": 172, "name": "Whitefield", "name_kn": "ವೈಟ್ಫೀಲ್ಡ್", "zone": "East", "lat": 12.9698, "lon": 77.7499},
    {"ward_number": 171, "name": "Marathahalli", "name_kn": "ಮಾರತ್ಹಲ್ಲಿ", "zone": "East", "lat": 12.9591, "lon": 77.7014},
    # West Bangalore
    {"ward_number": 112, "name": "Rajajinagar", "name_kn": "ರಾಜಾಜಿನಗರ", "zone": "West", "lat": 12.9985, "lon": 77.5477},
    {"ward_number": 111, "name": "Mahadevapura", "name_kn": "ಮಹಾದೇವಪುರ", "zone": "West", "lat": 13.0105, "lon": 77.5314},
    {"ward_number": 110, "name": "Malleshwaram", "name_kn": "ಮಲ್ಲೇಶ್ವರಂ", "zone": "North", "lat": 13.0037, "lon": 77.5709},
    {"ward_number": 109, "name": "Yeshwanthpur", "name_kn": "ಯಶವಂತಪುರ", "zone": "North", "lat": 13.0282, "lon": 77.5381},
    {"ward_number": 108, "name": "Hebbal", "name_kn": "ಹೆಬ್ಬಾಲ್", "zone": "North", "lat": 13.0358, "lon": 77.5970},
    # Central Bangalore
    {"ward_number": 85, "name": "Shivajinagar", "name_kn": "ಶಿವಾಜಿನಗರ", "zone": "Central", "lat": 12.9851, "lon": 77.6045},
    {"ward_number": 86, "name": "Frazer Town", "name_kn": "ಫ್ರೇಸರ್ ಟೌನ್", "zone": "Central", "lat": 12.9913, "lon": 77.6192},
    {"ward_number": 87, "name": "Cox Town", "name_kn": "ಕಾಕ್ಸ್ ಟೌನ್", "zone": "Central", "lat": 12.9913, "lon": 77.6352},
    {"ward_number": 88, "name": "Cooke Town", "name_kn": "ಕುಕ್ ಟೌನ್", "zone": "Central", "lat": 12.9821, "lon": 77.6438},
    {"ward_number": 89, "name": "Ulsoor", "name_kn": "ಉಲ್ಸೂರ್", "zone": "Central", "lat": 12.9843, "lon": 77.6058},
]

# Sample multilingual complaint texts
SAMPLE_COMPLAINTS = [
    # Roads - English
    ("Big pothole on main road near hsr sector 1", "roads", "en", "low"),
    ("Road damaged completely, cars getting stuck", "roads", "en", "high"),
    ("Pothole in front of house, needs immediate repair", "roads", "en", "medium"),
    # Roads - Hindi
    ("सड़क पर बड़ा गड्ढा है, गाड़ियां फंस रही हैं", "roads", "hi", "high"),
    ("रास्ते में गड्ढा है, दुर्घटना हो सकती है", "roads", "hi", "critical"),
    # Water - English
    ("Water pipeline leaking for 3 days", "water", "en", "medium"),
    ("No water supply in our area since yesterday", "water", "en", "high"),
    ("Water pipe burst, road flooded", "water", "en", "critical"),
    # Water - Hindi
    ("पानी की पाइप से लीक हो रहा है", "water", "hi", "medium"),
    ("पानी की आपूर्ति नहीं हो रही है", "water", "hi", "high"),
    # Waste - English
    ("Garbage not collected for a week", "waste", "en", "medium"),
    ("Dustbin overflow, bad smell in area", "waste", "en", "high"),
    ("Waste dumped on empty plot", "waste", "en", "medium"),
    # Waste - Hindi
    ("कचरा नहीं उठाया गया", "waste", "hi", "medium"),
    ("कचरे से बदबू आ रही है", "waste", "hi", "high"),
    # Streetlights - English
    ("Street light not working on our street", "streetlights", "en", "low"),
    ("Multiple street lights are broken", "streetlights", "en", "medium"),
    ("Area is dark, lights not working, safety risk", "streetlights", "en", "high"),
    # Drainage - English
    ("Drain blocked, water stagnating", "drainage", "en", "medium"),
    ("Drainage overflow on main road", "drainage", "en", "high"),
    ("Sewage water coming out of drain", "drainage", "en", "critical"),
    # Trees - English
    ("Tree branch fallen on road", "trees", "en", "medium"),
    ("Tree needs pruning, blocking signage", "trees", "en", "low"),
    ("Dangerous tree leaning on house", "trees", "en", "critical"),
]

# Department mapping
DEPARTMENTS = [
    {"name": "Roads & Infrastructure", "name_kn": "ರಸ್ತೆಗಳು ಮತ್ತು ಮೂಲಸೌಲಭ್ಯಗಳು", "description": "Road maintenance and infrastructure"},
    {"name": "Water Supply & Sewerage", "name_kn": "ನೀರು ಸರಬರಾಜು ಮತ್ತು ಕೊಳಚೆ ನಿರ್ವಹಣೆ", "description": "Water supply and sewage"},
    {"name": "Solid Waste Management", "name_kn": "ಘನ ತ್ಯಾಜ್ಯ ನಿರ್ವಹಣೆ", "description": "Garbage collection and disposal"},
    {"name": "Electrical & Street Lighting", "name_kn": "ವಿದ್ಯುತ್ ಮತ್ತು ಬೀದಿ ದೀಪಗಳು", "description": "Street lighting and electrical"},
    {"name": "Storm Water Drains", "name_kn": "ಮಳೆನೀರಿನ ಕಾಲುವೆಗಳು", "description": "Drainage system maintenance"},
    {"name": "Horticulture & Parks", "name_kn": "ತೋಟಗಿರಿ ಮತ್ತು ಉದ್ಯಾನಗಳು", "description": "Parks and tree maintenance"},
]

def seed_database():
    """Seed the database with initial data."""
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_wards = db.query(Ward).count()
        if existing_wards > 0:
            print(f"Database already has {existing_wards} wards. Skipping seed.")
            return

        print("Seeding departments...")
        for dept_data in DEPARTMENTS:
            dept = Department(**dept_data)
            db.add(dept)
        db.commit()
        print(f"  Created {len(DEPARTMENTS)} departments")

        print("Seeding wards...")
        for ward_data in BBMP_WARDS:
            ward = Ward(
                ward_number=ward_data["ward_number"],
                name=ward_data["name"],
                name_kn=ward_data.get("name_kn"),
                zone=ward_data.get("zone"),
                center_lat=ward_data["lat"],
                center_lon=ward_data["lon"],
                bbox_north=ward_data["lat"] + 0.02,
                bbox_south=ward_data["lat"] - 0.02,
                bbox_east=ward_data["lon"] + 0.02,
                bbox_west=ward_data["lon"] - 0.02
            )
            db.add(ward)
        db.commit()
        print(f"  Created {len(BBMP_WARDS)} wards")

        print("Seeding sample complaints...")
        complaints_created = 0

        # Get departments for mapping
        dept_map = {d.name: d.id for d in db.query(Department).all()}
        wards = db.query(Ward).all()
        ward_map = {w.ward_number: w for w in wards}

        for i, (text, category, lang, severity) in enumerate(SAMPLE_COMPLAINTS):
            # Random ward
            ward = random.choice(wards)

            # Generate complaint ID
            complaint_id = f"BBMP-2024-W{ward.ward_number:03d}-{i+1:05d}"

            # Get department
            dept_name = {
                "roads": "Roads & Infrastructure",
                "water": "Water Supply & Sewerage",
                "waste": "Solid Waste Management",
                "streetlights": "Electrical & Street Lighting",
                "drainage": "Storm Water Drains",
                "trees": "Horticulture & Parks"
            }.get(category, "Roads & Infrastructure")

            # Create complaint
            complaint = Complaint(
                complaint_id=complaint_id,
                text=text,
                language=lang,
                category=category,
                department_id=dept_map[dept_name],
                severity=SeverityLevel(severity),
                latitude=ward.center_lat + random.uniform(-0.005, 0.005),
                longitude=ward.center_lon + random.uniform(-0.005, 0.005),
                ward_id=ward.id,
                citizen_name=f"Citizen {i+1}",
                citizen_phone=f"9{random.randint(100000000, 999999999)}",
                status=ComplaintStatus.SUBMITTED,
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
            )
            db.add(complaint)

            # Create associated issue
            issue_id = f"ISS-{ward.ward_number:03d}-{i+1:04d}"
            issue = Issue(
                issue_id=issue_id,
                category=category,
                department_id=dept_map[dept_name],
                severity=SeverityLevel(severity),
                latitude=complaint.latitude,
                longitude=complaint.longitude,
                ward_id=ward.id,
                title=f"{category.capitalize()} issue in {ward.name}",
                description=text[:500],
                complaint_count=1,
                status=ComplaintStatus.SUBMITTED,
                created_at=complaint.created_at
            )
            db.add(issue)
            complaints_created += 1

            # Link complaint to issue
            db.flush()
            complaint.issue_id = issue.id

        db.commit()
        print(f"  Created {complaints_created} sample complaints with issues")

        print("\n✅ Database seeded successfully!")
        print(f"   - {len(DEPARTMENTS)} departments")
        print(f"   - {len(BBMP_WARDS)} wards")
        print(f"   - {complaints_created} complaints with issues")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
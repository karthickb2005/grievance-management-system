"""
Complaint submission and retrieval endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models import Complaint, Department, Ward, Issue, SeverityLevel, ComplaintStatus
from app.services.classifier import get_classifier
from app.services.geocoder import get_geo_service

router = APIRouter(prefix="/api/complaints", tags=["complaints"])

# Pydantic schemas
class ComplaintCreate(BaseModel):
    text: str = Field(..., min_length=10, max_length=5000)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    citizen_name: Optional[str] = None
    citizen_phone: Optional[str] = None

class ComplaintResponse(BaseModel):
    id: int
    complaint_id: str
    text: str
    language: str
    category: str
    department: str
    severity: str
    latitude: float
    longitude: float
    address: Optional[str]
    ward_number: Optional[int]
    ward_name: Optional[str]
    status: str
    issue_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=ComplaintResponse, status_code=201)
def submit_complaint(complaint: ComplaintCreate, db: Session = Depends(get_db)):
    """
    Submit a new complaint.

    - Detects language
    - Classifies into category and department
    - Scores severity
    - Checks for nearby issues to merge
    - Generates embeddings
    """
    classifier = get_classifier()
    geo_service = get_geo_service()

    # Detect language
    language = classifier.detect_language(complaint.text)

    # Classify complaint
    category, department_name, confidence = classifier.predict_category(complaint.text)

    # Score severity
    severity = classifier.score_severity(complaint.text, category)

    # Get or create department
    department = db.query(Department).filter_by(name=department_name).first()
    if not department:
        department = Department(name=department_name)
        db.add(department)
        db.flush()

    # Find ward (simplified - find nearest ward center)
    wards = db.query(Ward).all()
    nearest_ward = None
    min_distance = float('inf')

    for ward in wards:
        dist = geo_service.distance_meters(
            complaint.latitude, complaint.longitude,
            ward.center_lat, ward.center_lon
        )
        if dist < min_distance:
            min_distance = dist
            nearest_ward = ward

    # Generate complaint ID
    ward_num = nearest_ward.ward_number if nearest_ward else 0
    count = db.query(Complaint).filter_by(ward_id=nearest_ward.id if nearest_ward else None).count() + 1
    complaint_id = f"BBMP-2024-W{ward_num:03d}-{count:05d}"

    # Generate embedding
    embedding = classifier.get_embedding(complaint.text)

    # Create complaint record
    new_complaint = Complaint(
        complaint_id=complaint_id,
        text=complaint.text,
        language=language,
        category=category,
        department_id=department.id,
        severity=SeverityLevel(severity),
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        address=complaint.address,
        ward_id=nearest_ward.id if nearest_ward else None,
        citizen_name=complaint.citizen_name,
        citizen_phone=complaint.citizen_phone,
        status=ComplaintStatus.SUBMITTED,
        embedding=embedding
    )

    # Check for nearby issues to merge
    existing_issues = db.query(Issue).filter_by(
        category=category,
        status=ComplaintStatus.SUBMITTED
    ).all()

    issue_dicts = [{
        'id': issue.id,
        'category': issue.category,
        'latitude': issue.latitude,
        'longitude': issue.longitude
    } for issue in existing_issues]

    complaint_dict = {
        'category': category,
        'latitude': complaint.latitude,
        'longitude': complaint.longitude
    }

    merge_issue_id = geo_service.should_merge_to_issue(complaint_dict, issue_dicts)

    if merge_issue_id:
        # Merge into existing issue
        new_complaint.issue_id = merge_issue_id
        issue = db.query(Issue).get(merge_issue_id)
        issue.complaint_count += 1

        # Update issue centroid (simplified - just average)
        all_complaints = db.query(Complaint).filter_by(issue_id=merge_issue_id).all()
        lats = [c.latitude for c in all_complaints] + [complaint.latitude]
        lons = [c.longitude for c in all_complaints] + [complaint.longitude]
        issue.latitude = sum(lats) / len(lats)
        issue.longitude = sum(lons) / len(lons)
    else:
        # Create new issue
        issue_count = db.query(Issue).count() + 1
        issue_id = f"ISS-{ward_num:03d}-{issue_count:04d}"

        new_issue = Issue(
            issue_id=issue_id,
            category=category,
            department_id=department.id,
            severity=SeverityLevel(severity),
            latitude=complaint.latitude,
            longitude=complaint.longitude,
            ward_id=nearest_ward.id if nearest_ward else None,
            title=f"{category.capitalize()} issue",
            description=complaint.text[:500],
            complaint_count=1,
            status=ComplaintStatus.SUBMITTED
        )
        db.add(new_issue)
        db.flush()
        new_complaint.issue_id = new_issue.id

    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    return ComplaintResponse(
        id=new_complaint.id,
        complaint_id=new_complaint.complaint_id,
        text=new_complaint.text,
        language=new_complaint.language,
        category=new_complaint.category,
        department=department_name,
        severity=new_complaint.severity.value,
        latitude=new_complaint.latitude,
        longitude=new_complaint.longitude,
        address=new_complaint.address,
        ward_number=nearest_ward.ward_number if nearest_ward else None,
        ward_name=nearest_ward.name if nearest_ward else None,
        status=new_complaint.status.value,
        issue_id=new_complaint.issue_id,
        created_at=new_complaint.created_at
    )

@router.get("/", response_model=List[ComplaintResponse])
def list_complaints(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    ward: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List complaints with optional filters."""
    query = db.query(Complaint)

    if category:
        query = query.filter_by(category=category)
    if severity:
        query = query.filter_by(severity=SeverityLevel(severity))
    if ward:
        ward_obj = db.query(Ward).filter_by(ward_number=ward).first()
        if ward_obj:
            query = query.filter_by(ward_id=ward_obj.id)

    complaints = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for c in complaints:
        dept_name = c.department.name if c.department else "Unknown"
        ward_num = c.ward.ward_number if c.ward else None
        ward_name = c.ward.name if c.ward else None

        results.append(ComplaintResponse(
            id=c.id,
            complaint_id=c.complaint_id,
            text=c.text,
            language=c.language,
            category=c.category,
            department=dept_name,
            severity=c.severity.value,
            latitude=c.latitude,
            longitude=c.longitude,
            address=c.address,
            ward_number=ward_num,
            ward_name=ward_name,
            status=c.status.value,
            issue_id=c.issue_id,
            created_at=c.created_at
        ))

    return results

@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    """Get a specific complaint by ID."""
    complaint = db.query(Complaint).filter_by(complaint_id=complaint_id).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    dept_name = complaint.department.name if complaint.department else "Unknown"
    ward_num = complaint.ward.ward_number if complaint.ward else None
    ward_name = complaint.ward.name if complaint.ward else None

    return ComplaintResponse(
        id=complaint.id,
        complaint_id=complaint.complaint_id,
        text=complaint.text,
        language=complaint.language,
        category=complaint.category,
        department=dept_name,
        severity=complaint.severity.value,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        address=complaint.address,
        ward_number=ward_num,
        ward_name=ward_name,
        status=complaint.status.value,
        issue_id=complaint.issue_id,
        created_at=complaint.created_at
    )

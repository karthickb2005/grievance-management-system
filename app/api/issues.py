"""
Issue (merged complaints) endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Issue, Complaint, Ward, SeverityLevel, ComplaintStatus

router = APIRouter(prefix="/api/issues", tags=["issues"])

class IssueResponse(BaseModel):
    id: int
    issue_id: str
    category: str
    department: str
    severity: str
    latitude: float
    longitude: float
    ward_number: Optional[int]
    ward_name: Optional[str]
    title: str
    description: Optional[str]
    complaint_count: int
    status: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[IssueResponse])
def list_issues(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    ward: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List issues with optional filters."""
    query = db.query(Issue)

    if category:
        query = query.filter_by(category=category)
    if severity:
        query = query.filter_by(severity=SeverityLevel(severity))
    if ward:
        ward_obj = db.query(Ward).filter_by(ward_number=ward).first()
        if ward_obj:
            query = query.filter_by(ward_id=ward_obj.id)
    if status:
        query = query.filter_by(status=ComplaintStatus(status))

    issues = query.order_by(Issue.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for issue in issues:
        dept_name = issue.department.name if issue.department else "Unknown"
        ward_num = issue.ward.ward_number if issue.ward else None
        ward_name = issue.ward.name if issue.ward else None

        results.append(IssueResponse(
            id=issue.id,
            issue_id=issue.issue_id,
            category=issue.category,
            department=dept_name,
            severity=issue.severity.value,
            latitude=issue.latitude,
            longitude=issue.longitude,
            ward_number=ward_num,
            ward_name=ward_name,
            title=issue.title,
            description=issue.description,
            complaint_count=issue.complaint_count,
            status=issue.status.value,
            assigned_to=issue.assigned_to,
            created_at=issue.created_at,
            updated_at=issue.updated_at
        ))

    return results

@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(issue_id: str, db: Session = Depends(get_db)):
    """Get a specific issue by ID."""
    issue = db.query(Issue).filter_by(issue_id=issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    dept_name = issue.department.name if issue.department else "Unknown"
    ward_num = issue.ward.ward_number if issue.ward else None
    ward_name = issue.ward.name if issue.ward else None

    return IssueResponse(
        id=issue.id,
        issue_id=issue.issue_id,
        category=issue.category,
        department=dept_name,
        severity=issue.severity.value,
        latitude=issue.latitude,
        longitude=issue.longitude,
        ward_number=ward_num,
        ward_name=ward_name,
        title=issue.title,
        description=issue.description,
        complaint_count=issue.complaint_count,
        status=issue.status.value,
        assigned_to=issue.assigned_to,
        created_at=issue.created_at,
        updated_at=issue.updated_at
    )

@router.get("/{issue_id}/complaints", response_model=List[dict])
def get_issue_complaints(issue_id: str, db: Session = Depends(get_db)):
    """Get all complaints merged into an issue."""
    issue = db.query(Issue).filter_by(issue_id=issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    complaints = db.query(Complaint).filter_by(issue_id=issue.id).all()

    return [{
        "complaint_id": c.complaint_id,
        "text": c.text,
        "language": c.language,
        "latitude": c.latitude,
        "longitude": c.longitude,
        "created_at": c.created_at.isoformat()
    } for c in complaints]

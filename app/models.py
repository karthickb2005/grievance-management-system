from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    name_kn = Column(String(200))  # Kannada name
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Ward(Base):
    __tablename__ = "wards"

    id = Column(Integer, primary_key=True, index=True)
    ward_number = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_kn = Column(String(300))  # Kannada name
    zone = Column(String(100))
    # Simplified geometry - just center point for LITE mode
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    # Bounding box
    bbox_north = Column(Float)
    bbox_south = Column(Float)
    bbox_east = Column(Float)
    bbox_west = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(50), unique=True, nullable=False, index=True)  # BBMP-2024-W150-08942

    # Complaint content
    text = Column(Text, nullable=False)
    language = Column(String(10))  # en, hi, kn, ta, hi-en (Hinglish)

    # Classification
    category = Column(String(50), index=True)  # roads, water, waste, streetlights, drainage, trees
    department_id = Column(Integer, ForeignKey("departments.id"))
    severity = Column(SQLEnum(SeverityLevel), default=SeverityLevel.MEDIUM, index=True)

    # Geolocation
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(Text)
    ward_id = Column(Integer, ForeignKey("wards.id"), index=True)

    # Metadata
    citizen_name = Column(String(200))
    citizen_phone = Column(String(20))
    status = Column(SQLEnum(ComplaintStatus), default=ComplaintStatus.SUBMITTED, index=True)

    # Issue merging
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=True, index=True)

    # ML features
    embedding = Column(JSON)  # Store as JSON array for SQLite

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = relationship("Department", backref="complaints")
    ward = relationship("Ward", backref="complaints")
    issue = relationship("Issue", back_populates="complaints")

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String(50), unique=True, nullable=False, index=True)

    # Merged complaint details
    category = Column(String(50), index=True)
    department_id = Column(Integer, ForeignKey("departments.id"))
    severity = Column(SQLEnum(SeverityLevel), default=SeverityLevel.MEDIUM, index=True)

    # Representative location (centroid)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    ward_id = Column(Integer, ForeignKey("wards.id"), index=True)

    # Summary
    title = Column(String(500))
    description = Column(Text)
    complaint_count = Column(Integer, default=1)

    # Status
    status = Column(SQLEnum(ComplaintStatus), default=ComplaintStatus.SUBMITTED, index=True)
    assigned_to = Column(String(200))  # AEE name

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    department = relationship("Department", backref="issues")
    ward = relationship("Ward", backref="issues")
    complaints = relationship("Complaint", back_populates="issue")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(50), unique=True, nullable=False, index=True)

    # Alert details
    alert_type = Column(String(50), index=True)  # spike, cluster, sla_breach
    category = Column(String(50))
    ward_id = Column(Integer, ForeignKey("wards.id"), index=True)

    # Metrics
    complaint_count = Column(Integer)
    severity = Column(SQLEnum(SeverityLevel), default=SeverityLevel.HIGH)

    # Message
    title = Column(String(500))
    description = Column(Text)

    # Status
    acknowledged = Column(Integer, default=0)  # Boolean as int for SQLite
    resolved = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationship
    ward = relationship("Ward", backref="alerts")

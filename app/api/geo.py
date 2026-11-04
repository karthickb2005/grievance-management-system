"""
Geospatial endpoints for hex density and nearby queries.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Complaint
from app.services.geocoder import get_geo_service

router = APIRouter(prefix="/api/geo", tags=["geospatial"])

@router.get("/hex-density")
def get_hex_density(
    resolution: int = Query(9, ge=7, le=11),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get hexagonal density grid for map visualization.

    Args:
        resolution: Grid resolution (7-11, higher = smaller cells)
        category: Optional category filter

    Returns:
        GeoJSON FeatureCollection with complaint densities
    """
    query = db.query(Complaint)

    if category:
        query = query.filter_by(category=category)

    complaints = query.all()

    # Convert to dicts for geo service
    complaint_dicts = [{
        'latitude': c.latitude,
        'longitude': c.longitude,
        'severity': c.severity.value,
        'category': c.category
    } for c in complaints]

    geo_service = get_geo_service()
    geojson = geo_service.generate_hex_grid(complaint_dicts, resolution=resolution)

    return geojson

@router.get("/nearby")
def find_nearby_complaints(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: int = Query(500, ge=50, le=5000),
    db: Session = Depends(get_db)
):
    """
    Find complaints within radius of a location.

    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (50-5000)

    Returns:
        List of nearby complaints with distances
    """
    complaints = db.query(Complaint).all()

    # Convert to dicts
    complaint_dicts = [{
        'id': c.id,
        'complaint_id': c.complaint_id,
        'text': c.text,
        'category': c.category,
        'severity': c.severity.value,
        'latitude': c.latitude,
        'longitude': c.longitude,
        'created_at': c.created_at.isoformat()
    } for c in complaints]

    geo_service = get_geo_service()
    nearby = geo_service.find_nearby_complaints(lat, lon, complaint_dicts, radius)

    return nearby

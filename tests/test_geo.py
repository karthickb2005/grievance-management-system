"""
Unit tests for geospatial services.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.geocoder import GeoService

@pytest.fixture
def geo_service():
    """Create a geo service instance for testing."""
    return GeoService(merge_radius_meters=150)

def test_distance_calculation(geo_service):
    """Test distance calculation between two points."""
    # HSR Layout to Koramangala (approx 3km)
    lat1, lon1 = 12.9121, 77.6446
    lat2, lon2 = 12.9352, 77.6245

    distance = geo_service.distance_meters(lat1, lon1, lat2, lon2)
    assert 2500 < distance < 3500  # Approx 3km

    # Same point
    distance = geo_service.distance_meters(lat1, lon1, lat1, lon1)
    assert distance < 1  # Should be ~0

def test_find_nearby_complaints(geo_service):
    """Test finding nearby complaints."""
    # Test location: HSR Layout
    center_lat, center_lon = 12.9121, 77.6446

    complaints = [
        {'id': 1, 'latitude': 12.9121, 'longitude': 77.6446, 'category': 'roads'},  # Same location
        {'id': 2, 'latitude': 12.9125, 'longitude': 77.6450, 'category': 'water'},  # ~50m away
        {'id': 3, 'latitude': 12.9200, 'longitude': 77.6500, 'category': 'waste'},  # ~1km away
    ]

    # Find within 150m
    nearby = geo_service.find_nearby_complaints(center_lat, center_lon, complaints, radius_meters=150)
    assert len(nearby) == 2  # First two complaints
    assert nearby[0]['id'] == 1
    assert nearby[1]['id'] == 2

    # Find within 2km
    nearby = geo_service.find_nearby_complaints(center_lat, center_lon, complaints, radius_meters=2000)
    assert len(nearby) == 3  # All complaints

def test_compute_centroid(geo_service):
    """Test centroid calculation."""
    points = [
        (12.9121, 77.6446),
        (12.9125, 77.6450),
        (12.9119, 77.6442)
    ]

    center_lat, center_lon = geo_service.compute_centroid(points)
    assert 12.911 < center_lat < 12.913
    assert 77.644 < center_lon < 77.646

    # Empty list
    center_lat, center_lon = geo_service.compute_centroid([])
    assert center_lat == 0.0
    assert center_lon == 0.0

def test_should_merge_to_issue(geo_service):
    """Test issue merging logic."""
    new_complaint = {
        'latitude': 12.9121,
        'longitude': 77.6446,
        'category': 'roads'
    }

    existing_issues = [
        {'id': 1, 'latitude': 12.9122, 'longitude': 77.6447, 'category': 'roads'},  # Within 150m
        {'id': 2, 'latitude': 12.9200, 'longitude': 77.6500, 'category': 'roads'},  # Far away
        {'id': 3, 'latitude': 12.9121, 'longitude': 77.6446, 'category': 'water'},  # Same location, different category
    ]

    # Should merge with issue 1 (same category, close distance)
    merge_id = geo_service.should_merge_to_issue(new_complaint, existing_issues, same_category=True)
    assert merge_id == 1

    # Without category check, should still merge with issue 1 (closest)
    merge_id = geo_service.should_merge_to_issue(new_complaint, existing_issues, same_category=False)
    assert merge_id in [1, 3]  # Could merge with either

def test_generate_hex_grid(geo_service):
    """Test hex grid generation."""
    complaints = [
        {'latitude': 12.9121, 'longitude': 77.6446, 'severity': 'low', 'category': 'roads'},
        {'latitude': 12.9125, 'longitude': 77.6450, 'severity': 'high', 'category': 'water'},
        {'latitude': 12.9122, 'longitude': 77.6447, 'severity': 'medium', 'category': 'roads'},
    ]

    geojson = geo_service.generate_hex_grid(complaints, resolution=9)

    # Check GeoJSON structure
    assert geojson['type'] == 'FeatureCollection'
    assert 'features' in geojson
    assert len(geojson['features']) > 0

    # Check first feature
    feature = geojson['features'][0]
    assert feature['type'] == 'Feature'
    assert feature['geometry']['type'] == 'Polygon'
    assert 'count' in feature['properties']
    assert feature['properties']['count'] > 0

def test_detect_spatial_spike(geo_service):
    """Test spatial spike detection."""
    from datetime import datetime, timedelta

    now = datetime.utcnow()

    # Create complaints clustered in same area
    complaints = [
        {'latitude': 12.9121, 'longitude': 77.6446, 'category': 'water', 'created_at': now - timedelta(hours=1)},
        {'latitude': 12.9122, 'longitude': 77.6447, 'category': 'water', 'created_at': now - timedelta(hours=2)},
        {'latitude': 12.9123, 'longitude': 77.6448, 'category': 'water', 'created_at': now - timedelta(hours=3)},
        {'latitude': 12.9124, 'longitude': 77.6449, 'category': 'water', 'created_at': now - timedelta(hours=4)},
        {'latitude': 12.9125, 'longitude': 77.6450, 'category': 'water', 'created_at': now - timedelta(hours=5)},
    ]

    # Should detect spike (5 complaints in same area within 24 hours)
    spikes = geo_service.detect_spatial_spike(complaints, threshold=5, window_hours=24)
    assert len(spikes) > 0
    assert spikes[0]['count'] >= 5
    assert spikes[0]['category'] == 'water'

    # Lower threshold
    spikes = geo_service.detect_spatial_spike(complaints, threshold=3, window_hours=24)
    assert len(spikes) > 0

    # Too few complaints
    spikes = geo_service.detect_spatial_spike(complaints[:2], threshold=5, window_hours=24)
    assert len(spikes) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

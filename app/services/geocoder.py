"""
Geospatial services for complaint clustering and hex density visualization.
Uses simple lat/lon math for LITE mode (no PostGIS dependency).
"""
import math
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from geopy.distance import geodesic
from collections import defaultdict

class GeoService:
    def __init__(self, merge_radius_meters: int = 150):
        self.merge_radius_meters = merge_radius_meters

    def distance_meters(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters."""
        return geodesic((lat1, lon1), (lat2, lon2)).meters

    def find_nearby_complaints(
        self,
        latitude: float,
        longitude: float,
        complaints: List[Dict],
        radius_meters: Optional[int] = None
    ) -> List[Dict]:
        """
        Find complaints within radius of given location.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            complaints: List of complaint dicts with 'latitude', 'longitude' keys
            radius_meters: Search radius (defaults to merge_radius_meters)

        Returns:
            List of nearby complaints sorted by distance
        """
        if radius_meters is None:
            radius_meters = self.merge_radius_meters

        nearby = []
        for complaint in complaints:
            dist = self.distance_meters(
                latitude, longitude,
                complaint['latitude'], complaint['longitude']
            )
            if dist <= radius_meters:
                nearby.append({
                    **complaint,
                    'distance_meters': dist
                })

        # Sort by distance
        nearby.sort(key=lambda x: x['distance_meters'])
        return nearby

    def compute_centroid(self, points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Compute geographic centroid of a list of (lat, lon) points."""
        if not points:
            return (0.0, 0.0)

        lat_sum = sum(p[0] for p in points)
        lon_sum = sum(p[1] for p in points)
        count = len(points)

        return (lat_sum / count, lon_sum / count)

    def should_merge_to_issue(
        self,
        new_complaint: Dict,
        existing_issues: List[Dict],
        same_category: bool = True
    ) -> Optional[int]:
        """
        Check if a new complaint should merge into an existing issue.

        Args:
            new_complaint: Dict with 'latitude', 'longitude', 'category'
            existing_issues: List of issue dicts with same fields
            same_category: Only merge if categories match

        Returns:
            Issue ID to merge into, or None if no match
        """
        for issue in existing_issues:
            # Check category match
            if same_category and issue.get('category') != new_complaint.get('category'):
                continue

            # Check distance
            dist = self.distance_meters(
                new_complaint['latitude'], new_complaint['longitude'],
                issue['latitude'], issue['longitude']
            )

            if dist <= self.merge_radius_meters:
                return issue['id']

        return None

    def generate_hex_grid(
        self,
        complaints: List[Dict],
        resolution: int = 9
    ) -> Dict:
        """
        Generate hex density grid for visualization (H3-style binning).

        For LITE mode, we use a simplified grid approach without h3 library.
        This creates a regular hex-ish grid by rounding coordinates.

        Args:
            complaints: List of complaint dicts with 'latitude', 'longitude'
            resolution: Grid resolution (higher = smaller cells)

        Returns:
            GeoJSON FeatureCollection with hex densities
        """
        # Grid cell size (degrees) - smaller for higher resolution
        cell_size = 0.01 / (resolution / 9)  # ~1km at resolution 9

        # Bin complaints into grid cells
        grid = defaultdict(list)

        for complaint in complaints:
            lat = complaint['latitude']
            lon = complaint['longitude']

            # Round to grid cell
            cell_lat = round(lat / cell_size) * cell_size
            cell_lon = round(lon / cell_size) * cell_size

            grid[(cell_lat, cell_lon)].append(complaint)

        # Convert to GeoJSON features
        features = []
        for (cell_lat, cell_lon), cell_complaints in grid.items():
            count = len(cell_complaints)

            # Create hexagon-like polygon (simplified as square for now)
            half = cell_size / 2
            coordinates = [[
                [cell_lon - half, cell_lat - half],
                [cell_lon + half, cell_lat - half],
                [cell_lon + half, cell_lat + half],
                [cell_lon - half, cell_lat + half],
                [cell_lon - half, cell_lat - half]  # Close polygon
            ]]

            # Aggregate severity
            severity_counts = defaultdict(int)
            for c in cell_complaints:
                severity_counts[c.get('severity', 'low')] += 1

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates
                },
                "properties": {
                    "count": count,
                    "severity_low": severity_counts.get('low', 0),
                    "severity_medium": severity_counts.get('medium', 0),
                    "severity_high": severity_counts.get('high', 0),
                    "severity_critical": severity_counts.get('critical', 0),
                    "center_lat": cell_lat,
                    "center_lon": cell_lon
                }
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }

    def detect_spatial_spike(
        self,
        complaints: List[Dict],
        threshold: int = 5,
        window_hours: int = 24
    ) -> List[Dict]:
        """
        Detect spatial spikes (clusters of complaints in short time).

        Args:
            complaints: List of complaint dicts with location and timestamp
            threshold: Min complaints to trigger alert
            window_hours: Time window to check

        Returns:
            List of spike alerts with location and count
        """
        if len(complaints) < threshold:
            return []

        # Simple clustering by proximity
        clusters = []
        used = set()

        for i, complaint in enumerate(complaints):
            if i in used:
                continue

            # Find all nearby complaints within time window
            cluster = [complaint]
            used.add(i)

            for j, other in enumerate(complaints[i+1:], start=i+1):
                if j in used:
                    continue

                # Check distance
                dist = self.distance_meters(
                    complaint['latitude'], complaint['longitude'],
                    other['latitude'], other['longitude']
                )

                if dist <= self.merge_radius_meters * 2:  # Larger radius for spikes
                    # Check time window
                    time_diff = abs((complaint.get('created_at', datetime.utcnow()) -
                                   other.get('created_at', datetime.utcnow())).total_seconds() / 3600)

                    if time_diff <= window_hours:
                        cluster.append(other)
                        used.add(j)

            # Check if cluster meets threshold
            if len(cluster) >= threshold:
                # Compute cluster centroid
                points = [(c['latitude'], c['longitude']) for c in cluster]
                center_lat, center_lon = self.compute_centroid(points)

                # Get dominant category
                categories = [c.get('category', 'unknown') for c in cluster]
                dominant_category = max(set(categories), key=categories.count)

                clusters.append({
                    'center_lat': center_lat,
                    'center_lon': center_lon,
                    'count': len(cluster),
                    'category': dominant_category,
                    'complaints': cluster
                })

        return clusters

# Global instance
_geo_service = None

def get_geo_service(merge_radius_meters: int = 150) -> GeoService:
    """Get or create global geo service instance."""
    global _geo_service
    if _geo_service is None:
        _geo_service = GeoService(merge_radius_meters)
    return _geo_service

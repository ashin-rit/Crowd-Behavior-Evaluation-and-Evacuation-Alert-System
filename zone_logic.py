"""
================================================================================
ZONE LOGIC MODULE — DYNAMIC POLYGON ZONES
================================================================================
Handles polygon-based zone detection, density calculation, and status
classification for the Intelligent Crowd Behavior Evaluation System.

Uses a ray-casting algorithm for point-in-polygon detection with
percentage-based coordinates for resolution independence.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from config import DENSITY_THRESHOLDS


# ==============================================================================
# POINT-IN-POLYGON (RAY-CASTING ALGORITHM)
# ==============================================================================

def point_in_polygon(px: float, py: float, polygon_pct: List[Tuple[float, float]],
                     frame_w: int, frame_h: int) -> bool:
    """
    Determine if a pixel point (px, py) is inside a polygon defined
    by percentage-based vertices.

    Uses the ray-casting algorithm: cast a horizontal ray from the point
    and count how many polygon edges it crosses. Odd = inside, even = outside.

    Args:
        px: X coordinate of the point in pixels
        py: Y coordinate of the point in pixels
        polygon_pct: List of (x_pct, y_pct) vertices (0.0 to 1.0)
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        True if the point is inside the polygon
    """
    # Convert percentage vertices to pixel coordinates
    poly_px = [(v[0] * frame_w, v[1] * frame_h) for v in polygon_pct]
    n = len(poly_px)
    if n < 3:
        return False

    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly_px[i]
        xj, yj = poly_px[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i

    return inside


# ==============================================================================
# DETECTION ASSIGNMENT
# ==============================================================================

def assign_detections_to_zones(detections: List[Dict],
                                polygon_zones: List[Dict],
                                frame_w: int, frame_h: int) -> Dict[str, int]:
    """
    For each detected person, determine which polygon zone contains them.

    Args:
        detections: List of detection dicts with 'center': (cx, cy)
        polygon_zones: List of zone dicts with 'id' and 'polygon'
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        Dict mapping zone_id -> person count
    """
    zone_counts = {zone["id"]: 0 for zone in polygon_zones}

    for det in detections:
        cx, cy = det["center"]
        for zone in polygon_zones:
            if point_in_polygon(cx, cy, zone["polygon"], frame_w, frame_h):
                zone_counts[zone["id"]] += 1
                det["zone_id"] = zone["id"]
                break
        else:
            # Person not in any defined zone
            det["zone_id"] = None

    return zone_counts


# ==============================================================================
# DENSITY & STATUS CLASSIFICATION
# ==============================================================================

def calculate_density(count: int, area: float) -> float:
    """Calculate people per square meter."""
    if area <= 0:
        return 0.0
    return count / area


def get_status_by_density(density: float) -> str:
    """
    Classify a zone's status based on density.

    Returns: 'SAFE', 'MODERATE', 'WARNING', or 'EMERGENCY'
    """
    if density < DENSITY_THRESHOLDS["SAFE"]:
        return "SAFE"
    elif density < DENSITY_THRESHOLDS["MODERATE"]:
        return "MODERATE"
    elif density < DENSITY_THRESHOLDS["WARNING"]:
        return "WARNING"
    else:
        return "EMERGENCY"


def calculate_zone_statuses(zone_counts: Dict[str, int],
                             polygon_zones: List[Dict],
                             timer_manager=None) -> Tuple[Dict, Dict, Dict]:
    """
    Calculate density, status, and timer data for all dynamic zones.

    Args:
        zone_counts: Dict mapping zone_id -> person count
        polygon_zones: List of zone configuration dicts
        timer_manager: Optional EmergencyTimerManager instance

    Returns:
        Tuple of (zone_densities, zone_statuses, zone_timer_data)
        All dicts are keyed by zone_id (string).
    """
    zone_densities = {}
    zone_statuses = {}
    zone_timer_data = {}

    for zone in polygon_zones:
        zid = zone["id"]
        count = zone_counts.get(zid, 0)
        area = zone.get("area", 50)

        density = calculate_density(count, area)
        status = get_status_by_density(density)

        zone_densities[zid] = density
        zone_statuses[zid] = status

    # Timer management (emergency escalation)
    if timer_manager is not None:
        for zone in polygon_zones:
            zid = zone["id"]
            status = zone_statuses[zid]

            if status == "EMERGENCY":
                timer_manager.start_timer(zid)
            else:
                timer_manager.stop_timer(zid)

            timer_data = timer_manager.get_timer_data(zid)
            if timer_data:
                zone_timer_data[zid] = timer_data

    return zone_densities, zone_statuses, zone_timer_data


# ==============================================================================
# POLYGON UTILITIES
# ==============================================================================

def get_polygon_centroid(polygon_pct: List[Tuple[float, float]],
                          frame_w: int, frame_h: int) -> Tuple[int, int]:
    """
    Calculate the centroid of a polygon in pixel coordinates.

    Args:
        polygon_pct: List of (x_pct, y_pct) vertices
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        (cx, cy) centroid in pixel coordinates
    """
    if not polygon_pct:
        return (frame_w // 2, frame_h // 2)

    xs = [v[0] * frame_w for v in polygon_pct]
    ys = [v[1] * frame_h for v in polygon_pct]
    cx = int(sum(xs) / len(xs))
    cy = int(sum(ys) / len(ys))
    return (cx, cy)


def get_polygon_pixel_coords(polygon_pct: List[Tuple[float, float]],
                              frame_w: int, frame_h: int) -> np.ndarray:
    """
    Convert percentage polygon to numpy array of pixel coordinates.
    Suitable for OpenCV drawing functions.

    Args:
        polygon_pct: List of (x_pct, y_pct) vertices
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        np.ndarray of shape (N, 1, 2) for OpenCV polylines/fillPoly
    """
    pts = [(int(v[0] * frame_w), int(v[1] * frame_h)) for v in polygon_pct]
    return np.array(pts, dtype=np.int32).reshape((-1, 1, 2))


def get_global_alert_level(zone_statuses: Dict[str, str]) -> str:
    """
    Determine the overall system alert level from all zone statuses.

    Returns the highest severity status across all zones.
    """
    priority = {"SAFE": 0, "MODERATE": 1, "WARNING": 2, "EMERGENCY": 3}
    max_level = "SAFE"
    for status in zone_statuses.values():
        if priority.get(status, 0) > priority.get(max_level, 0):
            max_level = status
    return max_level
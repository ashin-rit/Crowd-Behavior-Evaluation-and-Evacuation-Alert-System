"""
================================================================================
EXIT LOGIC MODULE — SPATIAL EXIT POINTS
================================================================================
Manages spatial exit points with percentage-based coordinates.
Computes nearest-exit routing using Euclidean distance from zone centroids.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

import math
from typing import List, Dict, Tuple, Optional


# ==============================================================================
# COORDINATE CONVERSION
# ==============================================================================

def get_exit_pixel_coords(exit_point: Dict, frame_w: int, frame_h: int) -> Tuple[int, int]:
    """
    Convert an exit point's percentage coordinates to pixel coordinates.

    Args:
        exit_point: Exit dict with 'x_pct' and 'y_pct'
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        (x, y) in pixel coordinates
    """
    x = int(exit_point["x_pct"] * frame_w)
    y = int(exit_point["y_pct"] * frame_h)
    return (x, y)


# ==============================================================================
# EXIT STATUS MANAGEMENT
# ==============================================================================

def get_exit_statuses(exit_points: List[Dict]) -> Dict[str, str]:
    """
    Return current status of all exit points.

    Status is managed by the user via configuration (OPEN / BLOCKED).

    Args:
        exit_points: List of exit point dicts

    Returns:
        Dict mapping exit_id -> status string
    """
    return {ep["id"]: ep.get("status", "OPEN") for ep in exit_points}


# ==============================================================================
# NEAREST EXIT ROUTING
# ==============================================================================

def find_nearest_open_exit(zone_centroid_px: Tuple[int, int],
                            exit_points: List[Dict],
                            frame_w: int, frame_h: int) -> Optional[Dict]:
    """
    Find the nearest OPEN exit to a given zone centroid.

    Only considers exits with status == "OPEN".
    Uses Euclidean distance for proximity calculation.

    Args:
        zone_centroid_px: (cx, cy) centroid of the zone in pixel coords
        exit_points: List of exit point dicts
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        The nearest open exit dict, or None if no exits are open.
    """
    cx, cy = zone_centroid_px
    best_exit = None
    best_distance = float("inf")

    for ep in exit_points:
        if ep.get("status", "OPEN") != "OPEN":
            continue

        ex, ey = get_exit_pixel_coords(ep, frame_w, frame_h)
        dist = math.sqrt((cx - ex) ** 2 + (cy - ey) ** 2)

        if dist < best_distance:
            best_distance = dist
            best_exit = ep

    return best_exit


def find_nearest_exit_with_capacity(zone_centroid_px: Tuple[int, int],
                                     exit_points: List[Dict],
                                     frame_w: int, frame_h: int,
                                     zone_count: int = 0) -> Optional[Dict]:
    """
    Find the nearest OPEN exit, preferring exits with sufficient capacity.

    If the nearest exit's capacity is less than the zone's person count,
    it still returns that exit but logs a warning via the 'capacity_warning'
    key in the returned dict.

    Args:
        zone_centroid_px: (cx, cy) centroid of the zone in pixel coords
        exit_points: List of exit point dicts
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels
        zone_count: Number of people in the zone

    Returns:
        The nearest open exit dict (with optional 'capacity_warning'), or None.
    """
    nearest = find_nearest_open_exit(zone_centroid_px, exit_points, frame_w, frame_h)

    if nearest is not None and zone_count > nearest.get("capacity", 20):
        nearest = dict(nearest)  # Don't mutate original
        nearest["capacity_warning"] = True

    return nearest

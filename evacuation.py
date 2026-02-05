"""
================================================================================
EVACUATION MODULE — NEAREST EXIT ROUTING ENGINE
================================================================================
Generates context-aware evacuation instructions using dynamic polygon zones
and spatial exit points. Routes people to the nearest open exit via
centroid-based Euclidean distance calculation.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

from typing import List, Dict, Tuple, Optional
from zone_logic import get_polygon_centroid
from exit_logic import find_nearest_open_exit, get_exit_pixel_coords


# ==============================================================================
# EVACUATION INSTRUCTION GENERATION
# ==============================================================================

def generate_evacuation_instructions(polygon_zones: List[Dict],
                                      zone_statuses: Dict[str, str],
                                      zone_counts: Dict[str, int],
                                      zone_densities: Dict[str, float],
                                      exit_points: List[Dict],
                                      frame_w: int,
                                      frame_h: int) -> List[Dict]:
    """
    Generate evacuation instructions for all zones based on their status.

    Routing logic:
      - SAFE       → "Monitor"
      - MODERATE   → "Control flow"
      - WARNING    → "Prepare evacuation via [nearest open exit]"
      - EMERGENCY  → "EVACUATE via [nearest open exit]" or
                     "NO OPEN EXIT AVAILABLE"

    Args:
        polygon_zones: List of zone configuration dicts
        zone_statuses: Dict mapping zone_id -> status string
        zone_counts: Dict mapping zone_id -> person count
        zone_densities: Dict mapping zone_id -> density value
        exit_points: List of exit point dicts
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        List of instruction dicts, one per zone
    """
    instructions = []

    for zone in polygon_zones:
        zid = zone["id"]
        zone_name = zone.get("name", zid)
        status = zone_statuses.get(zid, "SAFE")
        count = zone_counts.get(zid, 0)
        density = zone_densities.get(zid, 0.0)

        # Compute zone centroid for routing
        centroid_px = get_polygon_centroid(zone["polygon"], frame_w, frame_h)

        selected_exit = None
        selected_exit_name = None

        if status == "SAFE":
            message = f"✅ {zone_name}: Normal. Continue monitoring."
            action = "MONITOR"

        elif status == "MODERATE":
            message = f"🔵 {zone_name}: Moderate density ({density:.1f}/m²). Control entry flow."
            action = "CONTROL"

        elif status == "WARNING":
            nearest = find_nearest_open_exit(centroid_px, exit_points, frame_w, frame_h)
            if nearest:
                selected_exit = nearest["id"]
                selected_exit_name = nearest.get("name", "Exit")
                message = f"⚠️ {zone_name}: High density! Prepare evacuation via {selected_exit_name}."
                action = "PREPARE"
            else:
                message = f"⚠️ {zone_name}: High density! All exits blocked — control crowd."
                action = "HOLD"

        else:  # EMERGENCY
            nearest = find_nearest_open_exit(centroid_px, exit_points, frame_w, frame_h)
            if nearest:
                selected_exit = nearest["id"]
                selected_exit_name = nearest.get("name", "Exit")
                cap_warning = ""
                if count > nearest.get("capacity", 20):
                    cap_warning = " (EXIT CAPACITY EXCEEDED)"
                message = f"🚨 EVACUATE {zone_name} via {selected_exit_name} IMMEDIATELY!{cap_warning}"
                action = "EVACUATE"
            else:
                message = f"🚨 CRITICAL: {zone_name} — NO OPEN EXIT AVAILABLE. AWAIT RESCUE!"
                action = "AWAIT_RESCUE"

        instructions.append({
            "zone_id": zid,
            "zone_name": zone_name,
            "status": status,
            "message": message,
            "action": action,
            "count": count,
            "density": density,
            "selected_exit": selected_exit_name,
            "selected_exit_id": selected_exit,
            "centroid_px": centroid_px,
        })

    return instructions


# ==============================================================================
# ROUTING DATA (FOR VISUALIZATION)
# ==============================================================================

def get_evacuation_routes(polygon_zones: List[Dict],
                           zone_statuses: Dict[str, str],
                           exit_points: List[Dict],
                           frame_w: int,
                           frame_h: int) -> List[Dict]:
    """
    Compute evacuation arrow data for zones in WARNING or EMERGENCY status.

    Returns a list of route dicts containing:
      - zone_id: source zone
      - centroid_px: (cx, cy) of the zone
      - exit_px: (ex, ey) of the selected exit
      - exit_name: name of the exit
      - severity: 'WARNING' or 'EMERGENCY'

    Used by the visualization layer to draw arrows.
    """
    routes = []

    for zone in polygon_zones:
        zid = zone["id"]
        status = zone_statuses.get(zid, "SAFE")

        if status not in ("WARNING", "EMERGENCY"):
            continue

        centroid_px = get_polygon_centroid(zone["polygon"], frame_w, frame_h)
        nearest = find_nearest_open_exit(centroid_px, exit_points, frame_w, frame_h)

        if nearest is None:
            continue

        exit_px = get_exit_pixel_coords(nearest, frame_w, frame_h)

        routes.append({
            "zone_id": zid,
            "centroid_px": centroid_px,
            "exit_px": exit_px,
            "exit_name": nearest.get("name", "Exit"),
            "severity": status,
        })

    return routes


# ==============================================================================
# GLOBAL ALERT LEVEL
# ==============================================================================

def get_global_alert_level(zone_statuses: Dict[str, str]) -> str:
    """
    Determine the overall system alert level.

    Returns the highest severity status across all zones.
    """
    priority = {"SAFE": 0, "MODERATE": 1, "WARNING": 2, "EMERGENCY": 3}
    max_level = "SAFE"
    for status in zone_statuses.values():
        if priority.get(status, 0) > priority.get(max_level, 0):
            max_level = status
    return max_level

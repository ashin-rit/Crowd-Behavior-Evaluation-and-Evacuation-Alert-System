"""
================================================================================
EVACUATION MODULE — ENHANCED ROUTING ENGINE
================================================================================
Generates context-aware evacuation instructions using dynamic polygon zones
and spatial exit points. Features:

  1. Priority Ranking    — Zones ranked by danger score (density × count)
  2. Exit Load Balancing — Prevents bottlenecks at a single exit
  3. Multi-Exit Splitting — Splits large crowds across multiple exits
  4. Estimated Evac Time — Distance-based time estimation

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

import math
from typing import List, Dict, Tuple, Optional
from zone_logic import get_polygon_centroid, get_global_alert_level
from exit_logic import (
    find_nearest_open_exit, get_exit_pixel_coords, find_ranked_open_exits
)
from config import (
    CROWD_WALK_SPEED_NORMAL, CROWD_WALK_SPEED_DENSE,
    DENSITY_SPEED_THRESHOLD, PIXELS_PER_METER
)


# ==============================================================================
# ESTIMATED EVACUATION TIME
# ==============================================================================

def _estimate_evacuation_time(distance_px: float, density: float) -> Tuple[float, float]:
    """
    Estimate evacuation time based on pixel distance and crowd density.

    Uses different walking speeds depending on density:
      - Normal speed (1.2 m/s) when density < 3.5 p/m²
      - Dense speed  (0.5 m/s) when density >= 3.5 p/m²

    Args:
        distance_px: Euclidean distance in pixels
        density: Current density in people per square meter

    Returns:
        Tuple of (est_time_seconds, distance_meters)
    """
    distance_m = distance_px / PIXELS_PER_METER

    if density >= DENSITY_SPEED_THRESHOLD:
        speed = CROWD_WALK_SPEED_DENSE
    else:
        speed = CROWD_WALK_SPEED_NORMAL

    if speed <= 0:
        return (0.0, distance_m)

    est_time = distance_m / speed
    return (round(est_time, 1), round(distance_m, 1))


# ==============================================================================
# PRIORITY RANKING
# ==============================================================================

def _rank_zones_by_danger(polygon_zones: List[Dict],
                           zone_statuses: Dict[str, str],
                           zone_counts: Dict[str, int],
                           zone_densities: Dict[str, float]) -> List[Dict]:
    """
    Rank zones by danger score (density × count), highest first.

    Only WARNING and EMERGENCY zones receive a priority number.
    SAFE and MODERATE zones are appended at the end with priority=None.

    Args:
        polygon_zones: List of zone configuration dicts
        zone_statuses: Dict mapping zone_id -> status
        zone_counts: Dict mapping zone_id -> person count
        zone_densities: Dict mapping zone_id -> density

    Returns:
        List of zone dicts augmented with 'danger_score' and 'priority'
    """
    danger_zones = []
    safe_zones = []

    for zone in polygon_zones:
        zid = zone["id"]
        status = zone_statuses.get(zid, "SAFE")
        count = zone_counts.get(zid, 0)
        density = zone_densities.get(zid, 0.0)
        danger_score = density * count

        enriched = dict(zone)
        enriched["danger_score"] = round(danger_score, 2)

        if status in ("WARNING", "EMERGENCY"):
            danger_zones.append(enriched)
        else:
            enriched["priority"] = None
            safe_zones.append(enriched)

    # Sort danger zones by score descending
    danger_zones.sort(key=lambda z: z["danger_score"], reverse=True)

    # Assign priority numbers (1 = most dangerous)
    for i, zone in enumerate(danger_zones):
        zone["priority"] = i + 1

    return danger_zones + safe_zones


# ==============================================================================
# EXIT LOAD BALANCING & MULTI-EXIT SPLITTING
# ==============================================================================

def _assign_exit_with_balancing(zone: Dict,
                                 zone_count: int,
                                 zone_density: float,
                                 exit_points: List[Dict],
                                 exit_load: Dict[str, int],
                                 centroid_px: Tuple[int, int],
                                 frame_w: int, frame_h: int) -> Dict:
    """
    Assign the best exit(s) for a zone considering load balancing and splitting.

    Logic:
      1. Get all open exits ranked by distance
      2. Find the best exit that still has remaining capacity
      3. If the zone's crowd exceeds the exit's remaining capacity,
         split across multiple exits

    Args:
        zone: Zone configuration dict
        zone_count: Number of people in this zone
        zone_density: Current density of this zone
        exit_points: List of all exit point dicts
        exit_load: Mutable dict tracking cumulative load per exit_id
        centroid_px: (cx, cy) zone centroid in pixels
        frame_w: Frame width
        frame_h: Frame height

    Returns:
        Dict with keys: primary_exit, split_routes, distance_px, est_time_seconds, distance_m
    """
    ranked_exits = find_ranked_open_exits(centroid_px, exit_points, frame_w, frame_h)

    if not ranked_exits:
        return {
            "primary_exit": None,
            "split_routes": [],
            "distance_px": 0,
            "est_time_seconds": 0,
            "distance_m": 0
        }

    # --- Try to find an exit with remaining capacity ---
    primary_exit = None
    for ex in ranked_exits:
        eid = ex["id"]
        capacity = ex.get("capacity", 20)
        current_load = exit_load.get(eid, 0)
        remaining = capacity - current_load

        if remaining > 0:
            primary_exit = ex
            break

    # If no exit has remaining capacity, use the nearest one anyway
    if primary_exit is None:
        primary_exit = ranked_exits[0]

    distance_px = primary_exit.get("distance_px", 0)
    est_time, distance_m = _estimate_evacuation_time(distance_px, zone_density)

    # --- Multi-exit splitting when crowd exceeds capacity ---
    split_routes = []
    primary_capacity = primary_exit.get("capacity", 20)
    primary_remaining = primary_capacity - exit_load.get(primary_exit["id"], 0)
    primary_remaining = max(primary_remaining, 0)

    if zone_count > primary_remaining and len(ranked_exits) > 1:
        # Split needed: assign as many as possible to primary, rest to others
        people_left = zone_count
        for ex in ranked_exits:
            if people_left <= 0:
                break

            eid = ex["id"]
            capacity = ex.get("capacity", 20)
            current_load_val = exit_load.get(eid, 0)
            available = max(capacity - current_load_val, 0)

            if available <= 0:
                continue

            assigned = min(people_left, available)
            split_routes.append({
                "exit_name": ex.get("name", "Exit"),
                "exit_id": eid,
                "people_count": assigned
            })
            exit_load[eid] = current_load_val + assigned
            people_left -= assigned

        # If still people left (all exits full), assign remainder to primary
        if people_left > 0:
            if split_routes:
                split_routes[0]["people_count"] += people_left
            else:
                split_routes.append({
                    "exit_name": primary_exit.get("name", "Exit"),
                    "exit_id": primary_exit["id"],
                    "people_count": people_left
                })
            exit_load[primary_exit["id"]] = exit_load.get(primary_exit["id"], 0) + people_left
    else:
        # No split needed, all to primary exit
        exit_load[primary_exit["id"]] = exit_load.get(primary_exit["id"], 0) + zone_count

    # Only include split_routes if there are actually multiple routes
    if len(split_routes) <= 1:
        split_routes = []

    return {
        "primary_exit": primary_exit,
        "split_routes": split_routes,
        "distance_px": distance_px,
        "est_time_seconds": est_time,
        "distance_m": distance_m
    }


# ==============================================================================
# EVACUATION INSTRUCTION GENERATION (ENHANCED)
# ==============================================================================

def generate_evacuation_instructions(polygon_zones: List[Dict],
                                      zone_statuses: Dict[str, str],
                                      zone_counts: Dict[str, int],
                                      zone_densities: Dict[str, float],
                                      exit_points: List[Dict],
                                      frame_w: int,
                                      frame_h: int) -> List[Dict]:
    """
    Generate enhanced evacuation instructions for all zones.

    Enhancements over basic version:
      1. Priority Ranking — zones sorted by danger score (density × count)
      2. Exit Load Balancing — high-priority zones get first pick of exits
      3. Multi-Exit Splitting — large crowds split across multiple exits
      4. Estimated Evacuation Time — distance-based time estimate

    Args:
        polygon_zones: List of zone configuration dicts
        zone_statuses: Dict mapping zone_id -> status string
        zone_counts: Dict mapping zone_id -> person count
        zone_densities: Dict mapping zone_id -> density value
        exit_points: List of exit point dicts
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        List of instruction dicts, one per zone, sorted by priority
    """
    # Step 1: Rank zones by danger score
    ranked_zones = _rank_zones_by_danger(
        polygon_zones, zone_statuses, zone_counts, zone_densities
    )

    # Step 2: Process zones in priority order with load tracking
    exit_load = {}  # Tracks cumulative people routed to each exit
    instructions = []

    for zone in ranked_zones:
        zid = zone["id"]
        zone_name = zone.get("name", zid)
        status = zone_statuses.get(zid, "SAFE")
        count = zone_counts.get(zid, 0)
        density = zone_densities.get(zid, 0.0)
        priority = zone.get("priority")
        danger_score = zone.get("danger_score", 0.0)

        centroid_px = get_polygon_centroid(zone["polygon"], frame_w, frame_h)

        # Defaults
        selected_exit = None
        selected_exit_name = None
        est_time = 0
        distance_m = 0
        split_routes = []

        if status == "SAFE":
            message = f"✅ {zone_name}: Normal. Continue monitoring."
            action = "MONITOR"

        elif status == "MODERATE":
            message = f"🔵 {zone_name}: Moderate density ({density:.1f}/m²). Control entry flow."
            action = "CONTROL"

        elif status == "WARNING":
            # Use load-balanced exit assignment
            assignment = _assign_exit_with_balancing(
                zone, count, density, exit_points, exit_load,
                centroid_px, frame_w, frame_h
            )

            if assignment["primary_exit"]:
                primary = assignment["primary_exit"]
                selected_exit = primary["id"]
                selected_exit_name = primary.get("name", "Exit")
                est_time = assignment["est_time_seconds"]
                distance_m = assignment["distance_m"]
                split_routes = assignment["split_routes"]

                time_str = f" (~{int(est_time)}s)" if est_time > 0 else ""
                if split_routes:
                    routes_str = " + ".join(
                        f"{r['people_count']} via {r['exit_name']}"
                        for r in split_routes
                    )
                    message = f"⚠️ {zone_name}: High density! Split evacuation: {routes_str}{time_str}"
                else:
                    message = f"⚠️ {zone_name}: High density! Prepare evacuation via {selected_exit_name}{time_str}."
                action = "PREPARE"
            else:
                message = f"⚠️ {zone_name}: High density! All exits blocked — control crowd."
                action = "HOLD"

        else:  # EMERGENCY
            assignment = _assign_exit_with_balancing(
                zone, count, density, exit_points, exit_load,
                centroid_px, frame_w, frame_h
            )

            if assignment["primary_exit"]:
                primary = assignment["primary_exit"]
                selected_exit = primary["id"]
                selected_exit_name = primary.get("name", "Exit")
                est_time = assignment["est_time_seconds"]
                distance_m = assignment["distance_m"]
                split_routes = assignment["split_routes"]

                time_str = f" (~{int(est_time)}s)" if est_time > 0 else ""
                cap_warning = ""
                if count > primary.get("capacity", 20) and not split_routes:
                    cap_warning = " (EXIT CAPACITY EXCEEDED)"

                if split_routes:
                    routes_str = " + ".join(
                        f"{r['people_count']} via {r['exit_name']}"
                        for r in split_routes
                    )
                    message = f"🚨 EVACUATE {zone_name}: Split across exits — {routes_str}{time_str}"
                else:
                    message = f"🚨 EVACUATE {zone_name} via {selected_exit_name} IMMEDIATELY!{time_str}{cap_warning}"
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
            # Enhanced fields
            "priority": priority,
            "danger_score": danger_score,
            "est_time_seconds": est_time,
            "distance_m": distance_m,
            "split_routes": split_routes,
        })

    return instructions


# ==============================================================================
# ROUTING DATA (FOR VISUALIZATION)
# ==============================================================================

def get_evacuation_routes(polygon_zones: List[Dict],
                           zone_statuses: Dict[str, str],
                           zone_counts: Dict[str, int],
                           zone_densities: Dict[str, float],
                           exit_points: List[Dict],
                           frame_w: int,
                           frame_h: int) -> List[Dict]:
    """
    Compute evacuation arrow data for zones in WARNING or EMERGENCY status.

    Uses the enhanced instruction engine so arrows reflect load-balanced routing.

    Returns a list of route dicts containing:
      - zone_id, centroid_px, exit_px, exit_name, severity
      - est_time_seconds (for display on arrows)
      - split_routes (for multi-arrow rendering)
    """
    instructions = generate_evacuation_instructions(
        polygon_zones, zone_statuses, zone_counts,
        zone_densities, exit_points, frame_w, frame_h
    )

    routes = []
    for instr in instructions:
        status = instr["status"]
        if status not in ("WARNING", "EMERGENCY"):
            continue

        if instr["selected_exit_id"] is None:
            continue

        centroid_px = instr["centroid_px"]

        # If split routes exist, draw arrows to each exit
        if instr["split_routes"]:
            for sr in instr["split_routes"]:
                # Find exit coords
                for ep in exit_points:
                    if ep["id"] == sr["exit_id"]:
                        exit_px = get_exit_pixel_coords(ep, frame_w, frame_h)
                        routes.append({
                            "zone_id": instr["zone_id"],
                            "centroid_px": centroid_px,
                            "exit_px": exit_px,
                            "exit_name": sr["exit_name"],
                            "severity": status,
                            "est_time_seconds": instr["est_time_seconds"],
                            "people_count": sr["people_count"],
                        })
                        break
        else:
            # Single exit route
            for ep in exit_points:
                if ep["id"] == instr["selected_exit_id"]:
                    exit_px = get_exit_pixel_coords(ep, frame_w, frame_h)
                    routes.append({
                        "zone_id": instr["zone_id"],
                        "centroid_px": centroid_px,
                        "exit_px": exit_px,
                        "exit_name": instr["selected_exit"],
                        "severity": status,
                        "est_time_seconds": instr["est_time_seconds"],
                        "people_count": instr["count"],
                    })
                    break

    return routes



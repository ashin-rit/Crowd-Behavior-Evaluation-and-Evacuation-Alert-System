"""
================================================================================
VISUALIZATION MODULE — POLYGON ZONES & SPATIAL EXITS
================================================================================
Handles all frame drawing operations including polygon zone overlays,
exit markers, evacuation arrows, HUD elements, bounding boxes, and
emergency timers.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple

from config import STATUS_COLORS_BGR, OVERLAY_ALPHA, EXIT_STATUS_COLORS_BGR
from zone_logic import (
    assign_detections_to_zones, calculate_zone_statuses,
    get_polygon_centroid, get_polygon_pixel_coords
)
from exit_logic import get_exit_pixel_coords, find_nearest_open_exit


# ==============================================================================
# POLYGON ZONE DRAWING
# ==============================================================================

def draw_polygon_zone(frame: np.ndarray, polygon_pct: List[Tuple[float, float]],
                      status: str, frame_w: int, frame_h: int) -> np.ndarray:
    """
    Draw a semi-transparent polygon overlay with status-based coloring.

    Args:
        frame: Video frame to draw on
        polygon_pct: List of (x_pct, y_pct) vertices
        status: Zone status string (SAFE/MODERATE/WARNING/EMERGENCY)
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        Frame with polygon overlay
    """
    pts = get_polygon_pixel_coords(polygon_pct, frame_w, frame_h)
    color = STATUS_COLORS_BGR.get(status, STATUS_COLORS_BGR["SAFE"])
    alpha = OVERLAY_ALPHA.get(status, 0.1)

    # Semi-transparent fill
    overlay = frame.copy()
    cv2.fillPoly(overlay, [pts], color)
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # Draw outline
    outline_thickness = 3 if status == "EMERGENCY" else 2
    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=outline_thickness)

    return frame


# ==============================================================================
# ZONE HUD (AT CENTROID)
# ==============================================================================

def draw_zone_hud_at_centroid(frame: np.ndarray, zone_name: str, count: int,
                               density: float, status: str,
                               centroid_px: Tuple[int, int]) -> np.ndarray:
    """
    Draw Heads-Up Display at the polygon's centroid.

    Shows zone name, people count, density, and status indicator.

    Args:
        frame: Video frame to draw on
        zone_name: Display name of the zone
        count: Number of people detected in zone
        density: Density in people/m²
        status: Current zone status string
        centroid_px: (cx, cy) centroid in pixel coordinates

    Returns:
        Frame with HUD overlay
    """
    cx, cy = centroid_px
    color = STATUS_COLORS_BGR.get(status, STATUS_COLORS_BGR["SAFE"])

    # Background
    bg_w, bg_h = 165, 75
    bg_x1 = cx - bg_w // 2
    bg_y1 = cy - bg_h // 2
    bg_x2 = cx + bg_w // 2
    bg_y2 = cy + bg_h // 2

    overlay = frame.copy()
    cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.65, frame, 0.35, 0)

    # Color accent bar on left
    cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x1 + 4, bg_y2), color, -1)

    # Text
    text_x = bg_x1 + 10
    text_y = bg_y1 + 20

    cv2.putText(frame, zone_name, (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)
    cv2.putText(frame, f"People: {count}", (text_x, text_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Density: {density:.2f}/m2", (text_x, text_y + 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    return frame


# ==============================================================================
# EXIT MARKERS
# ==============================================================================

def draw_exit_marker(frame: np.ndarray, exit_point: Dict,
                     frame_w: int, frame_h: int) -> np.ndarray:
    """
    Draw exit point marker on the frame.

    Green circle + label if OPEN, Red if BLOCKED.

    Args:
        frame: Video frame to draw on
        exit_point: Exit point dict with x_pct, y_pct, name, status
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        Frame with exit marker
    """
    ex, ey = get_exit_pixel_coords(exit_point, frame_w, frame_h)
    status = exit_point.get("status", "OPEN")
    name = exit_point.get("name", "Exit")
    color = EXIT_STATUS_COLORS_BGR.get(status, (0, 255, 0))

    # Draw outer circle
    cv2.circle(frame, (ex, ey), 18, color, 3)

    # Draw inner filled circle
    cv2.circle(frame, (ex, ey), 8, color, -1)

    # Draw exit icon (door symbol)
    cv2.putText(frame, "E", (ex - 5, ey + 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2, cv2.LINE_AA)

    # Draw name label
    label = f"{name} [{status}]"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    label_x = ex - tw // 2
    label_y = ey - 25

    # Label background
    overlay = frame.copy()
    cv2.rectangle(overlay, (label_x - 3, label_y - th - 3),
                  (label_x + tw + 3, label_y + 3), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

    cv2.putText(frame, label, (label_x, label_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    return frame


# ==============================================================================
# EVACUATION ARROWS
# ==============================================================================

def draw_evacuation_arrow(frame: np.ndarray,
                           centroid_px: Tuple[int, int],
                           exit_px: Tuple[int, int],
                           severity: str = "EMERGENCY") -> np.ndarray:
    """
    Draw an evacuation route arrow from zone centroid to the selected exit.

    Args:
        frame: Video frame to draw on
        centroid_px: (cx, cy) start point (zone centroid)
        exit_px: (ex, ey) end point (exit location)
        severity: 'WARNING' or 'EMERGENCY' for styling

    Returns:
        Frame with evacuation arrow
    """
    if severity == "EMERGENCY":
        color = (0, 0, 255)     # Red
        thickness = 3
    else:
        color = (0, 255, 255)   # Yellow
        thickness = 2

    # Draw arrowed line
    cv2.arrowedLine(frame, centroid_px, exit_px, color, thickness,
                    tipLength=0.04)

    # Draw direction label at midpoint
    mid_x = (centroid_px[0] + exit_px[0]) // 2
    mid_y = (centroid_px[1] + exit_px[1]) // 2

    label = "EVACUATE →" if severity == "EMERGENCY" else "PREPARE →"
    cv2.putText(frame, label, (mid_x - 40, mid_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)

    return frame


# ==============================================================================
# BOUNDING BOXES
# ==============================================================================

def draw_bounding_boxes(frame: np.ndarray, detections: List[Dict],
                        zone_statuses: Dict[str, str]) -> np.ndarray:
    """
    Draw bounding boxes around detected people.
    Box color determined by zone status.

    Args:
        frame: Video frame to draw on
        detections: List of detection dicts with 'bbox', 'zone_id', 'confidence'
        zone_statuses: Dict mapping zone_id -> status

    Returns:
        Frame with bounding boxes
    """
    for detection in detections:
        x1, y1, x2, y2 = detection['bbox']
        zone_id = detection.get('zone_id')
        confidence = detection.get('confidence', 0)
        status = zone_statuses.get(zone_id, "SAFE") if zone_id else "SAFE"
        color = STATUS_COLORS_BGR.get(status, STATUS_COLORS_BGR["SAFE"])

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = f"{confidence:.2f}"
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, color, 1, cv2.LINE_AA)

    return frame


# ==============================================================================
# EMERGENCY TIMERS (AT POLYGON CENTROID)
# ==============================================================================

def draw_emergency_timer_at_centroid(frame: np.ndarray, zone_name: str,
                                     timer_data: dict,
                                     centroid_px: Tuple[int, int]) -> np.ndarray:
    """
    Draw emergency timer overlay at a polygon centroid.

    Args:
        frame: Video frame to draw on
        zone_name: Name of the zone
        timer_data: Timer data dict from timer_manager
        centroid_px: (cx, cy) pixel position

    Returns:
        Frame with timer overlay
    """
    if not timer_data.get('active', False):
        return frame

    # Skip drawing during SEVERE flash-off
    if timer_data['severity'] == 'SEVERE' and not timer_data.get('flash', True):
        return frame

    cx, cy = centroid_px
    time_str = timer_data['formatted']
    severity = timer_data['severity']
    color = timer_data['color_bgr']

    # Position timer below the HUD
    y = cy + 55

    label = f"{zone_name} EMERGENCY: {time_str}"

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    font_thickness = 2

    (tw, th), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
    text_x = cx - tw // 2

    # Background
    pad = 6
    overlay = frame.copy()
    cv2.rectangle(overlay, (text_x - pad, y - th - pad),
                  (text_x + tw + pad, y + baseline + pad), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.8, frame, 0.2, 0)

    # Border
    border = 3 if severity == 'SEVERE' else 2
    cv2.rectangle(frame, (text_x - pad, y - th - pad),
                  (text_x + tw + pad, y + baseline + pad), color, border)

    # Text
    cv2.putText(frame, label, (text_x, y), font, font_scale,
                color, font_thickness, cv2.LINE_AA)

    # SEVERE warning
    if severity == 'SEVERE':
        warn = "CRITICAL RESPONSE DELAY!"
        (ww, wh), _ = cv2.getTextSize(warn, font, 0.5, 2)
        wx = cx - ww // 2
        wy = y + 25

        overlay = frame.copy()
        cv2.rectangle(overlay, (wx - 4, wy - wh - 4), (wx + ww + 4, wy + 4), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.8, frame, 0.2, 0)
        cv2.putText(frame, warn, (wx, wy), font, 0.5, (0, 0, 255), 2, cv2.LINE_AA)

    return frame


def draw_all_emergency_timers(frame: np.ndarray,
                               zone_timer_data: Dict[str, dict],
                               polygon_zones: List[Dict],
                               frame_w: int, frame_h: int) -> np.ndarray:
    """
    Draw emergency timers for all active emergency zones.

    Args:
        frame: Video frame to draw on
        zone_timer_data: Dict mapping zone_id -> timer data
        polygon_zones: List of zone dicts (for centroids)
        frame_w: Frame width in pixels
        frame_h: Frame height in pixels

    Returns:
        Frame with all timer overlays
    """
    zone_lookup = {z["id"]: z for z in polygon_zones}

    for zid, tdata in zone_timer_data.items():
        if not tdata.get('active', False):
            continue
        zone = zone_lookup.get(zid)
        if not zone:
            continue
        centroid = get_polygon_centroid(zone["polygon"], frame_w, frame_h)
        zone_name = zone.get("name", zid)
        frame = draw_emergency_timer_at_centroid(frame, zone_name, tdata, centroid)

    return frame


# ==============================================================================
# MAIN FRAME PROCESSING PIPELINE
# ==============================================================================

def process_frame(frame: np.ndarray, model,
                  polygon_zones: List[Dict],
                  exit_points: List[Dict],
                  timer_manager=None) -> Tuple:
    """
    Main processing function for each video frame.

    Pipeline:
    1. Run YOLO inference to detect people
    2. Assign detections to polygon zones
    3. Calculate zone densities and statuses
    4. Compute evacuation routes for emergency zones
    5. Draw all visualizations

    Args:
        frame: Input video frame (BGR format)
        model: Loaded YOLO model
        polygon_zones: List of polygon zone dicts
        exit_points: List of exit point dicts
        timer_manager: EmergencyTimerManager instance (optional)

    Returns:
        tuple: (processed_frame, detections, zone_counts, zone_densities,
                zone_statuses, zone_timer_data, evacuation_routes)
    """
    from evacuation import get_evacuation_routes

    frame_h, frame_w = frame.shape[:2]

    # 1. YOLO inference (class 0 = person)
    results = model(frame, classes=[0], verbose=False)

    # 2. Process detections
    detections = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            detections.append({
                'bbox': (x1, y1, x2, y2),
                'center': (cx, cy),
                'confidence': confidence
            })

    # 3. Assign to polygon zones
    zone_counts = assign_detections_to_zones(detections, polygon_zones, frame_w, frame_h)

    # 4. Calculate statuses
    zone_densities, zone_statuses, zone_timer_data = calculate_zone_statuses(
        zone_counts, polygon_zones, timer_manager
    )

    # 5. Compute evacuation routes
    evac_routes = get_evacuation_routes(polygon_zones, zone_statuses,
                                         exit_points, frame_w, frame_h)

    # ── DRAW VISUALIZATIONS ──────────────────────────────────────

    # a. Polygon zone overlays
    for zone in polygon_zones:
        zid = zone["id"]
        frame = draw_polygon_zone(frame, zone["polygon"],
                                  zone_statuses.get(zid, "SAFE"), frame_w, frame_h)

    # b. Bounding boxes
    frame = draw_bounding_boxes(frame, detections, zone_statuses)

    # c. Zone HUDs at centroids
    for zone in polygon_zones:
        zid = zone["id"]
        centroid = get_polygon_centroid(zone["polygon"], frame_w, frame_h)
        frame = draw_zone_hud_at_centroid(
            frame, zone.get("name", zid),
            zone_counts.get(zid, 0),
            zone_densities.get(zid, 0.0),
            zone_statuses.get(zid, "SAFE"),
            centroid
        )

    # d. Exit markers
    for ep in exit_points:
        frame = draw_exit_marker(frame, ep, frame_w, frame_h)

    # e. Evacuation arrows
    for route in evac_routes:
        frame = draw_evacuation_arrow(
            frame, route["centroid_px"], route["exit_px"], route["severity"]
        )

    # f. Emergency timers
    if timer_manager is not None and zone_timer_data:
        frame = draw_all_emergency_timers(
            frame, zone_timer_data, polygon_zones, frame_w, frame_h
        )

    return (frame, detections, zone_counts, zone_densities,
            zone_statuses, zone_timer_data, evac_routes)
"""
================================================================================
VISUALIZATION MODULE
================================================================================
Handles all frame drawing operations including heatmap overlays, zone grids,
HUD elements, bounding boxes, and emergency timers.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple

from config import STATUS_COLORS_BGR, OVERLAY_ALPHA
from zone_logic import get_zone


def draw_zone_overlay(frame: np.ndarray, zone: int, status: str,
                      frame_width: int, frame_height: int) -> np.ndarray:
    """
    Draw a semi-transparent heatmap overlay on the specified zone.
    
    The overlay color and transparency are determined by the zone's status:
    - SAFE: Green with low opacity
    - MODERATE: Blue with medium opacity
    - WARNING: Yellow with higher opacity
    - EMERGENCY: Red with highest opacity
    
    Args:
        frame: The video frame to draw on
        zone: Zone index (0-3)
        status: Current status of the zone
        frame_width: Width of the frame
        frame_height: Height of the frame
        
    Returns:
        np.ndarray: Frame with the overlay applied
    """
    mid_x = frame_width // 2
    mid_y = frame_height // 2
    
    # Determine zone coordinates
    zone_coords = {
        0: (0, 0, mid_x, mid_y),              # Top-Left
        1: (mid_x, 0, frame_width, mid_y),    # Top-Right
        2: (0, mid_y, mid_x, frame_height),   # Bottom-Left
        3: (mid_x, mid_y, frame_width, frame_height)  # Bottom-Right
    }
    
    x1, y1, x2, y2 = zone_coords[zone]
    
    # Create overlay
    overlay = frame.copy()
    color = STATUS_COLORS_BGR.get(status, STATUS_COLORS_BGR["SAFE"])
    alpha = OVERLAY_ALPHA.get(status, 0.1)
    
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    
    # Blend overlay with original frame
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
    
    return frame


def draw_zone_grid(frame: np.ndarray, frame_width: int, frame_height: int) -> np.ndarray:
    """
    Draw the 2x2 grid lines on the frame for visual zone separation.
    
    Args:
        frame: The video frame to draw on
        frame_width: Width of the frame
        frame_height: Height of the frame
        
    Returns:
        np.ndarray: Frame with grid lines
    """
    mid_x = frame_width // 2
    mid_y = frame_height // 2
    
    # Draw vertical line (center)
    cv2.line(frame, (mid_x, 0), (mid_x, frame_height), (255, 255, 255), 2)
    
    # Draw horizontal line (center)
    cv2.line(frame, (0, mid_y), (frame_width, mid_y), (255, 255, 255), 2)
    
    return frame


def draw_zone_hud(frame: np.ndarray, zone: int, count: int, density: float,
                  status: str, frame_width: int, frame_height: int,
                  zone_config: Dict) -> np.ndarray:
    """
    Draw the Heads-Up Display (HUD) showing zone info, count, and density.
    
    HUD shows:
    - Zone name
    - People count
    - Density (people/m²)
    - Status color indicator
    
    Args:
        frame: The video frame to draw on
        zone: Zone index (0-3)
        count: Number of people in the zone
        density: Density in people/m²
        status: Current status of the zone
        frame_width: Width of the frame
        frame_height: Height of the frame
        zone_config: Zone configuration dict
        
    Returns:
        np.ndarray: Frame with HUD elements
    """
    mid_x = frame_width // 2
    mid_y = frame_height // 2
    
    # HUD positions (top-left of each zone)
    hud_positions = {
        0: (10, 30),
        1: (mid_x + 10, 30),
        2: (10, mid_y + 30),
        3: (mid_x + 10, mid_y + 30)
    }
    
    x, y = hud_positions[zone]
    color = STATUS_COLORS_BGR.get(status, STATUS_COLORS_BGR["SAFE"])
    zone_name = zone_config.get(zone, {}).get("short", f"Zone {zone + 1}")
    
    # Draw background rectangle for HUD
    bg_width = 160
    bg_height = 75
    
    # Semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (x - 5, y - 25), (x + bg_width, y + bg_height - 25), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
    
    # Draw zone name
    cv2.putText(frame, zone_name, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, color, 2, cv2.LINE_AA)
    
    # Draw people count
    cv2.putText(frame, f"People: {count}", (x, y + 22), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Draw density
    cv2.putText(frame, f"Density: {density:.2f}/m2", (x, y + 42), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1, cv2.LINE_AA)
    
    return frame


def draw_emergency_timer(frame: np.ndarray, zone: int, timer_data: dict,
                        frame_width: int, frame_height: int) -> np.ndarray:
    """
    Draw emergency timer overlay for a specific zone.
    
    Displays:
    - Zone number
    - Elapsed time in MM:SS format
    - Color-coded based on severity (Yellow → Orange → Red)
    - Flashing effect for SEVERE (60+ seconds)
    - Critical delay warning for 60+ seconds
    
    Args:
        frame: Video frame to draw on
        zone: Zone index (0-3)
        timer_data: Timer information dict from timer_manager
        frame_width: Width of the frame
        frame_height: Height of the frame
        
    Returns:
        np.ndarray: Frame with timer overlay
    """
    if not timer_data.get('active', False):
        return frame
    
    # Skip drawing if in SEVERE flash-off state
    if timer_data['severity'] == 'SEVERE' and not timer_data.get('flash', True):
        return frame
    
    mid_x = frame_width // 2
    mid_y = frame_height // 2
    
    # Timer positions (bottom of each zone, centered)
    timer_positions = {
        0: (mid_x // 4, mid_y - 60),           # Top-Left zone
        1: (mid_x + mid_x // 4, mid_y - 60),   # Top-Right zone
        2: (mid_x // 4, frame_height - 60),    # Bottom-Left zone
        3: (mid_x + mid_x // 4, frame_height - 60)  # Bottom-Right zone
    }
    
    x, y = timer_positions[zone]
    
    # Get timer info
    time_str = timer_data['formatted']
    severity = timer_data['severity']
    color = timer_data['color_bgr']
    
    # Create timer label
    label = f"ZONE {zone + 1} EMERGENCY: {time_str}"
    
    # Font settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    font_thickness = 2
    
    # Get text size for background
    (text_width, text_height), baseline = cv2.getTextSize(
        label, font, font_scale, font_thickness
    )
    
    # Center the text
    text_x = x - text_width // 2
    text_y = y
    
    # Draw background rectangle
    padding = 8
    bg_x1 = text_x - padding
    bg_y1 = text_y - text_height - padding
    bg_x2 = text_x + text_width + padding
    bg_y2 = text_y + baseline + padding
    
    overlay = frame.copy()
    cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.8, frame, 0.2, 0)
    
    # Draw colored border
    border_thickness = 3 if severity == 'SEVERE' else 2
    cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), color, border_thickness)
    
    # Draw timer text
    cv2.putText(frame, label, (text_x, text_y), font, font_scale, 
                color, font_thickness, cv2.LINE_AA)
    
    # Add escalation warning for SEVERE cases (60+ seconds)
    if severity == 'SEVERE':
        warning_text = "CRITICAL RESPONSE DELAY!"
        warning_y = text_y + 28
        
        (warn_width, warn_height), _ = cv2.getTextSize(
            warning_text, font, 0.6, 2
        )
        warn_x = x - warn_width // 2
        
        # Draw warning background
        warn_bg_x1 = warn_x - 5
        warn_bg_y1 = warning_y - warn_height - 5
        warn_bg_x2 = warn_x + warn_width + 5
        warn_bg_y2 = warning_y + 5
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (warn_bg_x1, warn_bg_y1), 
                     (warn_bg_x2, warn_bg_y2), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.8, frame, 0.2, 0)
        
        # Draw warning text
        cv2.putText(frame, warning_text, (warn_x, warning_y), 
                   font, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
    
    return frame


def draw_all_emergency_timers(frame: np.ndarray, zone_timer_data: Dict[int, dict],
                              frame_width: int, frame_height: int) -> np.ndarray:
    """
    Draw emergency timers for all zones with active emergencies.
    
    Args:
        frame: Video frame to draw on
        zone_timer_data: Dict mapping zone index to timer data
        frame_width: Width of the frame
        frame_height: Height of the frame
        
    Returns:
        np.ndarray: Frame with all timer overlays
    """
    for zone, timer_data in zone_timer_data.items():
        if timer_data.get('active', False):
            frame = draw_emergency_timer(frame, zone, timer_data, 
                                        frame_width, frame_height)
    
    return frame


def draw_bounding_boxes(frame: np.ndarray, detections: List[Dict],
                        zone_statuses: Dict[int, str]) -> np.ndarray:
    """
    Draw bounding boxes around detected people.
    
    Box color is determined by the status of the zone they're in.
    
    Args:
        frame: The video frame to draw on
        detections: List of detection dictionaries
        zone_statuses: Dict mapping zone to status
        
    Returns:
        np.ndarray: Frame with bounding boxes
    """
    for detection in detections:
        x1, y1, x2, y2 = detection['bbox']
        zone = detection.get('zone', 0)
        confidence = detection.get('confidence', 0)
        status = zone_statuses.get(zone, "SAFE")
        color = STATUS_COLORS_BGR.get(status, STATUS_COLORS_BGR["SAFE"])
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw confidence label
        label = f"{confidence:.2f}"
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, color, 1, cv2.LINE_AA)
    
    return frame


def process_frame(frame: np.ndarray, model, zone_config: Dict, 
                 timer_manager=None) -> Tuple:
    """
    Main processing function for each video frame.
    
    Pipeline:
    1. Run YOLO inference to detect people
    2. Calculate zone counts and densities
    3. Manage emergency timers
    4. Draw visualizations
    
    Args:
        frame: Input video frame (BGR format)
        model: Loaded YOLO model
        zone_config: Zone configuration with areas
        timer_manager: EmergencyTimerManager instance (optional)
        
    Returns:
        tuple: (processed_frame, detections, zone_counts, zone_densities, 
                zone_statuses, zone_timer_data)
    """
    from zone_logic import calculate_zone_statuses
    
    frame_height, frame_width = frame.shape[:2]
    
    # Run YOLO inference (class 0 = person)
    results = model(frame, classes=[0], verbose=False)
    
    # Process detections
    detections = []
    zone_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            
            # Calculate center point
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            
            # Determine zone
            zone = get_zone(cx, cy, frame_width, frame_height)
            zone_counts[zone] += 1
            
            detections.append({
                'bbox': (x1, y1, x2, y2),
                'center': (cx, cy),
                'zone': zone,
                'confidence': confidence
            })
    
    # Calculate statuses with timer management
    zone_densities, zone_statuses, zone_timer_data = calculate_zone_statuses(
        zone_counts, zone_config, timer_manager
    )
    
    # Draw visualizations
    # 1. Heatmap overlays
    for zone in range(4):
        frame = draw_zone_overlay(frame, zone, zone_statuses[zone],
                                  frame_width, frame_height)
    
    # 2. Bounding boxes
    frame = draw_bounding_boxes(frame, detections, zone_statuses)
    
    # 3. Grid lines
    frame = draw_zone_grid(frame, frame_width, frame_height)
    
    # 4. HUD for each zone
    for zone in range(4):
        frame = draw_zone_hud(frame, zone, zone_counts[zone],
                              zone_densities[zone], zone_statuses[zone],
                              frame_width, frame_height, zone_config)
    
    # 5. Emergency timers (if timer_manager provided)
    if timer_manager is not None and zone_timer_data:
        frame = draw_all_emergency_timers(frame, zone_timer_data, 
                                         frame_width, frame_height)
    
    return frame, detections, zone_counts, zone_densities, zone_statuses, zone_timer_data


# ============================================================================
# WRAPPER FUNCTIONS FOR APP.PY COMPATIBILITY
# ============================================================================

def draw_zone_grid_wrapper(frame: np.ndarray, zone_boundaries: Dict) -> np.ndarray:
    """
    Wrapper function for draw_zone_grid to match app.py's expected signature.
    
    Args:
        frame: Video frame
        zone_boundaries: Dictionary of zone boundaries (not used, for API compatibility)
        
    Returns:
        Frame with grid lines drawn
    """
    frame_height, frame_width = frame.shape[:2]
    return draw_zone_grid(frame, frame_width, frame_height)


def draw_density_heatmap(frame: np.ndarray, zone_densities: Dict[int, float], 
                        zone_boundaries: Dict) -> np.ndarray:
    """
    Draw density heatmap overlay for all zones.
    
    Creates semi-transparent colored overlays on each zone based on their
    density status (SAFE=green, MODERATE=blue, WARNING=yellow, EMERGENCY=red).
    
    Args:
        frame: Video frame to draw on
        zone_densities: Dict mapping zone index to density value
        zone_boundaries: Dict of zone boundaries (not used, frame dimensions derived)
        
    Returns:
        Frame with heatmap overlays
    """
    from zone_logic import get_status_by_density
    
    frame_height, frame_width = frame.shape[:2]
    
    for zone, density in zone_densities.items():
        status = get_status_by_density(density)
        frame = draw_zone_overlay(frame, zone, status, frame_width, frame_height)
    
    return frame


def draw_exit_status(frame: np.ndarray, exit_statuses: Dict[int, str], 
                    exit_config: List[Dict]) -> np.ndarray:
    """
    Draw exit status indicators on the frame.
    
    Displays the status of each exit (OPEN/CROWDED/BLOCKED) at the top
    of the frame with color-coded indicators.
    
    Args:
        frame: Video frame to draw on
        exit_statuses: Dict mapping exit index to status string
        exit_config: List of exit configuration dictionaries
        
    Returns:
        Frame with exit status indicators
    """
    from config import EXIT_STATUS_COLORS
    
    # Define colors for each status (BGR format)
    status_colors_bgr = {
        "OPEN": (0, 255, 0),      # Green
        "CROWDED": (0, 165, 255),  # Orange
        "BLOCKED": (0, 0, 255)     # Red
    }
    
    # Draw exit statuses at the top of the frame
    y_offset = 30
    x_start = 10
    
    for idx, exit_info in enumerate(exit_config):
        if idx >= len(exit_statuses):
            break
            
        status = exit_statuses.get(idx, "OPEN")
        exit_name = exit_info.get("name", f"Exit {idx + 1}")
        direction = exit_info.get("direction", "")
        color = status_colors_bgr.get(status, (255, 255, 255))
        
        # Draw semi-transparent background
        text = f"{exit_name} ({direction}): {status}"
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (x_start - 5, y_offset - text_height - 5), 
                     (x_start + text_width + 5, y_offset + 5), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        
        # Draw text
        cv2.putText(frame, text, (x_start, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
        
        y_offset += 35
    
    return frame
"""
================================================================================
VISUALIZATION MODULE
================================================================================
Handles all frame drawing operations including heatmap overlays, zone grids,
HUD elements, and bounding boxes.

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


def process_frame(frame: np.ndarray, model, zone_config: Dict) -> Tuple:
    """
    Main processing function for each video frame.
    
    Pipeline:
    1. Run YOLO inference to detect people
    2. Calculate zone counts and densities
    3. Draw visualizations
    
    Args:
        frame: Input video frame (BGR format)
        model: Loaded YOLO model
        zone_config: Zone configuration with areas
        
    Returns:
        tuple: (processed_frame, detections, zone_counts, zone_densities, zone_statuses)
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
    
    # Calculate statuses
    zone_densities, zone_statuses = calculate_zone_statuses(zone_counts, zone_config)
    
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
    
    return frame, detections, zone_counts, zone_densities, zone_statuses

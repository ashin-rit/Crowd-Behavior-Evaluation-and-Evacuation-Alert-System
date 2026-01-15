"""
Visualization functions for drawing overlays, grids, and HUDs.
"""
import cv2
import numpy as np
from config import STATUS_COLORS_BGR, OVERLAY_ALPHA, ZONE_CONFIG

def draw_zone_overlay(frame: np.ndarray, zone: int, status: str, 
                      frame_width: int, frame_height: int) -> np.ndarray:
    """
    Draw a semi-transparent heatmap overlay on the specified zone.
    
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
        0: (0, 0, mid_x, mid_y),           # Top-Left
        1: (mid_x, 0, frame_width, mid_y),  # Top-Right
        2: (0, mid_y, mid_x, frame_height), # Bottom-Left
        3: (mid_x, mid_y, frame_width, frame_height)  # Bottom-Right
    }
    
    x1, y1, x2, y2 = zone_coords[zone]
    
    # Create overlay
    overlay = frame.copy()
    color = STATUS_COLORS_BGR[status]
    alpha = OVERLAY_ALPHA[status]
    
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


def draw_zone_hud(frame: np.ndarray, zone: int, count: int, status: str,
                  frame_width: int, frame_height: int) -> np.ndarray:
    """
    Draw the Heads-Up Display (HUD) showing zone name and people count.
    
    Args:
        frame: The video frame to draw on
        zone: Zone index (0-3)
        count: Number of people in the zone
        status: Current status of the zone
        frame_width: Width of the frame
        frame_height: Height of the frame
        
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
    color = STATUS_COLORS_BGR[status]
    zone_name = ZONE_CONFIG[zone]["short"]
    
    # Draw background rectangle for HUD
    bg_width = 150
    bg_height = 60
    
    # Semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (x - 5, y - 25), (x + bg_width, y + bg_height - 20), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)
    
    # Draw zone name
    cv2.putText(frame, zone_name, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, color, 2, cv2.LINE_AA)
    
    # Draw people count
    cv2.putText(frame, f"People: {count}", (x, y + 25), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255, 255, 255), 2, cv2.LINE_AA)
    
    return frame

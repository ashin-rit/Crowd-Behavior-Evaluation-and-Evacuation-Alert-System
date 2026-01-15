"""
Core business logic and calculations for the Crowd Behavior Evaluation System.
"""
from config import ZONE_CONFIG

def get_zone(cx: int, cy: int, frame_width: int, frame_height: int) -> int:
    """
    Determine which zone (0-3) a point belongs to based on 2x2 grid division.
    
    Args:
        cx: X-coordinate of the point (center of bounding box)
        cy: Y-coordinate of the point (center of bounding box)
        frame_width: Width of the video frame
        frame_height: Height of the video frame
        
    Returns:
        int: Zone index (0, 1, 2, or 3)
    """
    mid_x = frame_width // 2
    mid_y = frame_height // 2
    
    # Determine zone based on quadrant
    if cx < mid_x:
        if cy < mid_y:
            return 0  # Top-Left
        else:
            return 2  # Bottom-Left
    else:
        if cy < mid_y:
            return 1  # Top-Right
        else:
            return 3  # Bottom-Right


def get_status(count: int, threshold: int) -> str:
    """
    Determine the status based on count and threshold using Traffic Light logic.
    
    Args:
        count: Number of people detected in the zone
        threshold: Maximum safe capacity for the zone
        
    Returns:
        str: Status string ("SAFE", "WARNING", or "EMERGENCY")
    """
    if threshold == 0:
        return "SAFE"
    
    percentage = (count / threshold) * 100
    
    if percentage <= 50:
        return "SAFE"
    elif percentage <= 85:
        return "WARNING"
    else:
        return "EMERGENCY"


def generate_instructions(zone_statuses: dict, zone_counts: dict) -> list:
    """
    Generate evacuation instructions based on zone statuses.
    
    Args:
        zone_statuses: Dict mapping zone index to status
        zone_counts: Dict mapping zone index to people count
        
    Returns:
        list: List of instruction dictionaries with zone, status, message, and count
    """
    instructions = []
    
    for zone in range(4):
        status = zone_statuses[zone]
        zone_name = ZONE_CONFIG[zone]["name"]
        exit_name = ZONE_CONFIG[zone]["exit"]
        count = zone_counts[zone]
        
        if status == "SAFE":
            message = f"✅ {zone_name}: Status Normal. Monitoring..."
        elif status == "WARNING":
            message = f"⚠️ {zone_name}: High Density Detected. Slow down entry."
        else:  # EMERGENCY
            message = f"🚨 CRITICAL: EVACUATE {zone_name} via {exit_name}!"
        
        instructions.append({
            'zone': zone,
            'status': status,
            'message': message,
            'count': count
        })
    
    return instructions

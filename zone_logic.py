"""
================================================================================
ZONE LOGIC MODULE
================================================================================
Handles zone detection, density calculation, and zone classification.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

from config import DENSITY_THRESHOLDS


def get_zone(cx: int, cy: int, frame_width: int, frame_height: int) -> int:
    """
    Determine which zone (0-3) a point belongs to based on 2x2 grid division.
    
    ZONE DIVISION LOGIC:
    ====================
    The frame is divided into 4 equal quadrants using the center point:
    
        +-------------------+-------------------+
        |                   |                   |
        |      Zone 0       |      Zone 1       |
        |    (Top-Left)     |    (Top-Right)    |
        |                   |                   |
        +---------+---------+---------+---------+
        |                   |                   |
        |      Zone 2       |      Zone 3       |
        |   (Bottom-Left)   |   (Bottom-Right)  |
        |                   |                   |
        +-------------------+-------------------+
    
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


def calculate_density(count: int, area: float) -> float:
    """
    Calculate crowd density in people per square meter.
    
    DENSITY FORMULA:
    ================
    Density (ρ) = Number of People / Area (m²)
    
    This is the key metric for safety assessment, as it accounts for
    different zone sizes and provides a standardized measure.
    
    Args:
        count: Number of people detected in the zone
        area: Zone area in square meters
        
    Returns:
        float: Density in people per square meter
    """
    if area <= 0:
        return 0.0
    return count / area


def get_status_by_density(density: float) -> str:
    """
    Classify zone status based on density thresholds.
    
    CLASSIFICATION LEVELS:
    ======================
    1. SAFE (< 2 people/m²)
       - Comfortable movement possible
       - Normal monitoring
       
    2. MODERATE (2 - 3.5 people/m²)
       - Movement becoming restricted
       - Control entry flow
       
    3. WARNING (3.5 - 5 people/m²)
       - Very restricted movement
       - Risk of crushing, prepare evacuation
       
    4. EMERGENCY (> 5 people/m²)
       - Dangerous density
       - Immediate evacuation required
    
    Args:
        density: Crowd density in people/m²
        
    Returns:
        str: Status classification ("SAFE", "MODERATE", "WARNING", or "EMERGENCY")
    """
    if density < DENSITY_THRESHOLDS["SAFE"]:
        return "SAFE"
    elif density < DENSITY_THRESHOLDS["MODERATE"]:
        return "MODERATE"
    elif density < DENSITY_THRESHOLDS["WARNING"]:
        return "WARNING"
    else:
        return "EMERGENCY"


def get_zone_counts_from_detections(detections: list, frame_width: int, frame_height: int) -> dict:
    """
    Count people in each zone based on their bounding box centers.
    
    Args:
        detections: List of detection dictionaries with 'center' key
        frame_width: Width of the video frame
        frame_height: Height of the video frame
        
    Returns:
        dict: Zone index (0-3) mapped to people count
    """
    zone_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    
    for detection in detections:
        cx, cy = detection['center']
        zone = get_zone(cx, cy, frame_width, frame_height)
        zone_counts[zone] += 1
        detection['zone'] = zone  # Add zone info to detection
    
    return zone_counts


def calculate_zone_statuses(zone_counts: dict, zone_config: dict) -> tuple:
    """
    Calculate status for each zone based on density.
    
    Args:
        zone_counts: Dict mapping zone index to people count
        zone_config: Dict with zone configuration including area
        
    Returns:
        tuple: (zone_densities, zone_statuses)
            - zone_densities: Dict mapping zone to density value
            - zone_statuses: Dict mapping zone to status string
    """
    zone_densities = {}
    zone_statuses = {}
    
    for zone in range(4):
        count = zone_counts.get(zone, 0)
        area = zone_config.get(zone, {}).get("area", 50)
        
        density = calculate_density(count, area)
        status = get_status_by_density(density)
        
        zone_densities[zone] = density
        zone_statuses[zone] = status
    
    return zone_densities, zone_statuses

"""
================================================================================
EXIT LOGIC MODULE
================================================================================
Handles exit configuration, zone-to-exit mapping, and exit status calculation.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

from typing import List, Dict, Optional


def get_zone_exit_mapping(exit_config: List[Dict]) -> Dict[int, Dict]:
    """
    Generate primary and secondary exit mapping for each zone.
    
    MAPPING LOGIC:
    ==============
    Each zone is mapped to:
    1. Primary Exit - First exit that includes this zone
    2. Secondary Exit - Next available exit (fallback if primary is unsafe)
    
    This enables intelligent routing during evacuations:
    - If primary exit is blocked, redirect to secondary
    - Reduces congestion at single exit points
    
    Args:
        exit_config: List of exit configuration dictionaries
                    Each has: id, name, direction, capacity, zones
        
    Returns:
        dict: Zone index mapped to {primary: exit_index, secondary: exit_index}
              exit_index is None if no exit is available
    """
    mapping = {}
    
    for zone in range(4):
        primary = None
        secondary = None
        
        # Find exits that serve this zone
        for idx, exit_info in enumerate(exit_config):
            if zone in exit_info.get("zones", []):
                if primary is None:
                    primary = idx
                elif secondary is None:
                    secondary = idx
                    break
        
        mapping[zone] = {
            "primary": primary,
            "secondary": secondary
        }
    
    return mapping


def get_exit_status(exit_config: List[Dict], zone_statuses: Dict[int, str]) -> Dict[int, str]:
    """
    Determine exit status based on the statuses of associated zones.
    
    EXIT STATUS LOGIC:
    ==================
    The status of an exit depends on the conditions in its associated zones:
    
    1. OPEN (Green)
       - All associated zones are SAFE or MODERATE
       - Exit can be used normally
       
    2. CROWDED (Orange)
       - At least one zone is in WARNING status
       - Exit usable but with caution, consider alternatives
       
    3. BLOCKED (Red)
       - At least one zone is in EMERGENCY status
       - Exit should NOT be used, dangerous congestion
    
    Args:
        exit_config: List of exit configurations
        zone_statuses: Dict mapping zone index to status string
        
    Returns:
        dict: Exit index mapped to status ("OPEN", "CROWDED", "BLOCKED")
    """
    exit_statuses = {}
    
    for idx, exit_info in enumerate(exit_config):
        zones = exit_info.get("zones", [])
        zone_stats = [zone_statuses.get(z, "SAFE") for z in zones]
        
        # Priority: EMERGENCY > WARNING > others
        if "EMERGENCY" in zone_stats:
            exit_statuses[idx] = "BLOCKED"
        elif "WARNING" in zone_stats:
            exit_statuses[idx] = "CROWDED"
        else:
            exit_statuses[idx] = "OPEN"
    
    return exit_statuses


def get_best_exit_for_zone(zone: int, exit_config: List[Dict], 
                           zone_exit_mapping: Dict, exit_statuses: Dict) -> Optional[Dict]:
    """
    Find the best available exit for a given zone.
    
    Priority:
    1. Primary exit if OPEN
    2. Secondary exit if OPEN
    3. Primary exit if CROWDED (better than nothing)
    4. Secondary exit if CROWDED
    5. None if all exits are BLOCKED
    
    Args:
        zone: Zone index (0-3)
        exit_config: List of exit configurations
        zone_exit_mapping: Mapping from zone to primary/secondary exits
        exit_statuses: Current status of each exit
        
    Returns:
        dict: Best exit configuration, or None if all blocked
    """
    mapping = zone_exit_mapping.get(zone, {})
    primary_idx = mapping.get("primary")
    secondary_idx = mapping.get("secondary")
    
    # Check primary exit first
    if primary_idx is not None:
        if exit_statuses.get(primary_idx) == "OPEN":
            return exit_config[primary_idx]
    
    # Check secondary exit
    if secondary_idx is not None:
        if exit_statuses.get(secondary_idx) == "OPEN":
            return exit_config[secondary_idx]
    
    # Fall back to crowded exits (better than blocked)
    if primary_idx is not None:
        if exit_statuses.get(primary_idx) == "CROWDED":
            return exit_config[primary_idx]
    
    if secondary_idx is not None:
        if exit_statuses.get(secondary_idx) == "CROWDED":
            return exit_config[secondary_idx]
    
    return None

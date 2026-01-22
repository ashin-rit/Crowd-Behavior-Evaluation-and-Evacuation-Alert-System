"""
================================================================================
EVACUATION INSTRUCTIONS MODULE
================================================================================
Generates context-aware evacuation instructions based on zone status,
exit availability, and crowd conditions.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

from typing import List, Dict
from exit_logic import get_best_exit_for_zone


def generate_instructions(zone_statuses: Dict[int, str],
                          zone_counts: Dict[int, int],
                          zone_densities: Dict[int, float],
                          zone_config: Dict,
                          exit_config: List[Dict],
                          zone_exit_mapping: Dict,
                          exit_statuses: Dict[int, str]) -> List[Dict]:
    """
    Generate context-aware evacuation instructions for each zone.
    
    INSTRUCTION LOGIC:
    ==================
    Instructions are generated based on:
    1. Zone's current status (SAFE/MODERATE/WARNING/EMERGENCY)
    2. Exit availability (OPEN/CROWDED/BLOCKED)
    3. Fallback routing when primary exit is unavailable
    
    INSTRUCTION TYPES:
    ==================
    - SAFE: "Normal. Continue monitoring."
    - MODERATE: "Control entry flow."
    - WARNING: "Prepare evacuation via [Exit]" or "REDIRECT to [Alt Exit]"
    - EMERGENCY: "EVACUATE via [Exit] IMMEDIATELY!" or "AWAIT RESCUE"
    
    Args:
        zone_statuses: Dict mapping zone to status string
        zone_counts: Dict mapping zone to people count
        zone_densities: Dict mapping zone to density value
        zone_config: Zone configuration with names
        exit_config: List of exit configurations
        zone_exit_mapping: Zone to exit mapping
        exit_statuses: Current status of each exit
        
    Returns:
        list: List of instruction dictionaries with zone, status, message, etc.
    """
    instructions = []
    
    for zone in range(4):
        status = zone_statuses.get(zone, "SAFE")
        zone_name = zone_config.get(zone, {}).get("name", f"Zone {zone + 1}")
        count = zone_counts.get(zone, 0)
        density = zone_densities.get(zone, 0.0)
        
        # Get mapping info
        mapping = zone_exit_mapping.get(zone, {})
        primary_idx = mapping.get("primary")
        secondary_idx = mapping.get("secondary")
        
        # Get exit names
        primary_exit_name = None
        secondary_exit_name = None
        primary_status = None
        secondary_status = None
        
        if primary_idx is not None and primary_idx < len(exit_config):
            primary_exit_name = exit_config[primary_idx].get("name", "Primary Exit")
            primary_status = exit_statuses.get(primary_idx, "OPEN")
            
        if secondary_idx is not None and secondary_idx < len(exit_config):
            secondary_exit_name = exit_config[secondary_idx].get("name", "Secondary Exit")
            secondary_status = exit_statuses.get(secondary_idx, "OPEN")
        
        # Generate message based on status
        if status == "SAFE":
            message = f"✅ {zone_name}: Normal. Continue monitoring."
            action = "MONITOR"
            
        elif status == "MODERATE":
            message = f"🔵 {zone_name}: Moderate density ({density:.1f}/m²). Control entry flow."
            action = "CONTROL"
            
        elif status == "WARNING":
            if primary_status == "OPEN" and primary_exit_name:
                message = f"⚠️ {zone_name}: High density! Prepare evacuation via {primary_exit_name}."
                action = "PREPARE"
            elif secondary_status == "OPEN" and secondary_exit_name:
                message = f"⚠️ {zone_name}: REDIRECT to {secondary_exit_name} (primary exit crowded)."
                action = "REDIRECT"
            elif primary_status == "CROWDED" and primary_exit_name:
                message = f"⚠️ {zone_name}: High density! Use {primary_exit_name} with caution."
                action = "CAUTION"
            else:
                message = f"⚠️ {zone_name}: High density! All exits congested - control crowd."
                action = "HOLD"
                
        else:  # EMERGENCY
            if primary_status == "OPEN" and primary_exit_name:
                message = f"🚨 EVACUATE {zone_name} via {primary_exit_name} IMMEDIATELY!"
                action = "EVACUATE"
            elif secondary_status == "OPEN" and secondary_exit_name:
                message = f"🚨 EVACUATE {zone_name} via {secondary_exit_name} (alternate route)!"
                action = "EVACUATE_ALT"
            elif primary_status == "CROWDED" and primary_exit_name:
                message = f"🚨 EMERGENCY: {zone_name} - Use {primary_exit_name} (congested but passable)!"
                action = "EVACUATE_CROWDED"
            elif secondary_status == "CROWDED" and secondary_exit_name:
                message = f"🚨 EMERGENCY: {zone_name} - Use {secondary_exit_name} (congested)!"
                action = "EVACUATE_CROWDED"
            else:
                message = f"🚨 CRITICAL: {zone_name} - AWAIT RESCUE. All exits blocked!"
                action = "AWAIT_RESCUE"
        
        instructions.append({
            "zone": zone,
            "status": status,
            "message": message,
            "action": action,
            "count": count,
            "density": density,
            "primary_exit": primary_exit_name,
            "secondary_exit": secondary_exit_name
        })
    
    return instructions


def get_global_alert_level(zone_statuses: Dict[int, str]) -> str:
    """
    Determine the overall alert level based on all zone statuses.
    
    Args:
        zone_statuses: Dict mapping zone to status
        
    Returns:
        str: Global alert level (highest severity among all zones)
    """
    statuses = list(zone_statuses.values())
    
    if "EMERGENCY" in statuses:
        return "EMERGENCY"
    elif "WARNING" in statuses:
        return "WARNING"
    elif "MODERATE" in statuses:
        return "MODERATE"
    else:
        return "SAFE"


def get_summary_message(zone_statuses: Dict[int, str], 
                        zone_counts: Dict[int, int]) -> str:
    """
    Generate a summary message for the current crowd state.
    
    Args:
        zone_statuses: Dict mapping zone to status
        zone_counts: Dict mapping zone to count
        
    Returns:
        str: Summary message for display
    """
    total_people = sum(zone_counts.values())
    alert_level = get_global_alert_level(zone_statuses)
    
    emergency_zones = [z for z, s in zone_statuses.items() if s == "EMERGENCY"]
    warning_zones = [z for z, s in zone_statuses.items() if s == "WARNING"]
    
    if alert_level == "EMERGENCY":
        zones_str = ", ".join([f"Zone {z+1}" for z in emergency_zones])
        return f"🚨 EMERGENCY in {zones_str}! Total: {total_people} people"
    elif alert_level == "WARNING":
        zones_str = ", ".join([f"Zone {z+1}" for z in warning_zones])
        return f"⚠️ Warning in {zones_str}. Total: {total_people} people"
    elif alert_level == "MODERATE":
        return f"🔵 Moderate density detected. Total: {total_people} people"
    else:
        return f"✅ All zones safe. Total: {total_people} people"


def generate_evacuation_instructions(zone_statuses: Dict[int, str], 
                                     zone_exit_mapping: Dict, 
                                     exit_config: List[Dict]) -> List[Dict]:
    """
    Wrapper function for app.py compatibility.
    
    Adapts the signature expected by app.py to call the actual generate_instructions function.
    
    Args:
        zone_statuses: Dict mapping zone to status string
        zone_exit_mapping: Zone to exit mapping
        exit_config: List of exit configurations
        
    Returns:
        list: List of instruction dictionaries formatted for app.py
    """
    from exit_logic import get_exit_status
    
    # Create zone_counts and zone_densities (estimated from statuses)
    zone_counts = {z: 0 for z in range(4)}
    zone_densities = {z: 0.0 for z in range(4)}
    
    # Estimate counts based on status for display purposes
    status_to_count = {
        "SAFE": 5,
        "MODERATE": 20,
        "WARNING": 40,
        "EMERGENCY": 60
    }
    
    for zone, status in zone_statuses.items():
        zone_counts[zone] = status_to_count.get(status, 0)
        zone_densities[zone] = zone_counts[zone] / 50.0  # Assuming 50m² zones
    
    # Create zone config
    zone_config = {
        0: {"name": "Zone 1 (Top-Left)", "area": 50},
        1: {"name": "Zone 2 (Top-Right)", "area": 50},
        2: {"name": "Zone 3 (Bottom-Left)", "area": 50},
        3: {"name": "Zone 4 (Bottom-Right)", "area": 50}
    }
    
    # Get exit statuses
    exit_statuses = get_exit_status(exit_config, zone_statuses)
    
    # Call actual implementation
    instructions = generate_instructions(
        zone_statuses, zone_counts, zone_densities,
        zone_config, exit_config, zone_exit_mapping, exit_statuses
    )
    
    # Format for app.py (simplify structure)
    formatted_instructions = []
    for instr in instructions:
        formatted_instructions.append({
            'zone': f"Zone {instr['zone'] + 1}",
            'instruction': instr['message']
        })
    
    return formatted_instructions


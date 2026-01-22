"""
================================================================================
CONFIGURATION MODULE
================================================================================
Contains all constants, default configurations, and threshold values for the
Intelligent Crowd Behavior Evaluation & Evacuation System.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

# ==============================================================================
# ZONE CONFIGURATION DEFAULTS
# ==============================================================================

# Default zone configuration with area in square meters
# These can be customized by the user at runtime
DEFAULT_ZONE_CONFIG = {
    0: {"name": "Zone 1 (Top-Left)", "area": 50, "short": "Zone 1"},
    1: {"name": "Zone 2 (Top-Right)", "area": 50, "short": "Zone 2"},
    2: {"name": "Zone 3 (Bottom-Left)", "area": 50, "short": "Zone 3"},
    3: {"name": "Zone 4 (Bottom-Right)", "area": 50, "short": "Zone 4"}
}

# ==============================================================================
# EXIT CONFIGURATION DEFAULTS
# ==============================================================================

# Default exit configuration (user can add 1-8 exits)
# Each exit has: name, direction, capacity, and associated zones
DEFAULT_EXIT_CONFIG = [
    {
        "id": "exit_0",
        "name": "Main Gate",
        "direction": "North",
        "capacity": 20,
        "zones": [0, 1]  # Top zones exit via North
    },
    {
        "id": "exit_1",
        "name": "South Exit",
        "direction": "South",
        "capacity": 20,
        "zones": [2, 3]  # Bottom zones exit via South
    }
]

# ==============================================================================
# DENSITY THRESHOLDS (people per square meter)
# ==============================================================================

# Based on crowd safety research:
# - < 2 people/m²: Comfortable movement
# - 2-3.5 people/m²: Restricted movement
# - 3.5-5 people/m²: Very restricted, risk of crushing
# - > 5 people/m²: Dangerous, immediate action required

DENSITY_THRESHOLDS = {
    "SAFE": 2.0,        # Below this = Safe
    "MODERATE": 3.5,    # Below this = Moderate
    "WARNING": 5.0,     # Below this = Warning
    # Above WARNING threshold = Emergency
}

# ==============================================================================
# STATUS COLORS
# ==============================================================================

# BGR format for OpenCV drawing
STATUS_COLORS_BGR = {
    "SAFE": (0, 255, 0),         # Green
    "MODERATE": (255, 191, 0),   # Cyan/Blue
    "WARNING": (0, 255, 255),    # Yellow
    "EMERGENCY": (0, 0, 255)     # Red
}

# HEX format for Streamlit UI
STATUS_COLORS_HEX = {
    "SAFE": "#00FF00",
    "MODERATE": "#00BFFF",
    "WARNING": "#FFFF00",
    "EMERGENCY": "#FF0000"
}

# Overlay alpha values for heatmap intensity
OVERLAY_ALPHA = {
    "SAFE": 0.1,
    "MODERATE": 0.15,
    "WARNING": 0.25,
    "EMERGENCY": 0.35
}

# ==============================================================================
# EXIT STATUS COLORS
# ==============================================================================

EXIT_STATUS_COLORS = {
    "OPEN": "#00FF00",      # Green - safe to use
    "CROWDED": "#FFA500",   # Orange - use with caution
    "BLOCKED": "#FF0000"    # Red - do not use
}

# ==============================================================================
# UI CONFIGURATION
# ==============================================================================

# Maximum number of exits user can configure
MAX_EXITS = 8

# Minimum number of exits required
MIN_EXITS = 1

# Default number of exits
DEFAULT_NUM_EXITS = 2

# Zone area limits (square meters)
MIN_ZONE_AREA = 10
MAX_ZONE_AREA = 500
DEFAULT_ZONE_AREA = 50

# Direction options for exits
EXIT_DIRECTIONS = ["North", "South", "East", "West", "Northeast", "Northwest", "Southeast", "Southwest"]

# Add these constants to your existing config.py

# ============================================
# EMERGENCY TIMER CONFIGURATION
# ============================================
TIMER_THRESHOLDS = {
    'WARNING': 30,      # 0-30 seconds: Yellow
    'CRITICAL': 60,     # 30-60 seconds: Orange
    'SEVERE': 60        # 60+ seconds: Red flashing
}

TIMER_COLORS = {
    'WARNING': (0, 255, 255),      # Yellow (BGR)
    'CRITICAL': (0, 165, 255),     # Orange (BGR)
    'SEVERE': (0, 0, 255)          # Red (BGR)
}

# Timer display settings
TIMER_FONT_SCALE = 0.7
TIMER_FONT_THICKNESS = 2
TIMER_FLASH_INTERVAL = 0.5  # Seconds between flashes for SEVERE state
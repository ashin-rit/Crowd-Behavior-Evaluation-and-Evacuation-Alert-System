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
# YOLO MODEL CONFIGURATION
# ==============================================================================

# Path to the trained YOLO weights file
YOLO_MODEL_PATH = 'models/crowdeval_best.pt'

# ==============================================================================
# POLYGON ZONE CONFIGURATION DEFAULTS
# ==============================================================================

# Default polygon zones — percentage-based coordinates (0.0 to 1.0)
# These match the original 2x2 grid layout as a starting point
DEFAULT_POLYGON_ZONES = [
    {
        "id": "zone_0",
        "name": "Zone A (Top-Left)",
        "area": 50,  # square meters
        "polygon": [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)],
    },
    {
        "id": "zone_1",
        "name": "Zone B (Top-Right)",
        "area": 50,
        "polygon": [(0.5, 0.0), (1.0, 0.0), (1.0, 0.5), (0.5, 0.5)],
    },
    {
        "id": "zone_2",
        "name": "Zone C (Bottom-Left)",
        "area": 50,
        "polygon": [(0.0, 0.5), (0.5, 0.5), (0.5, 1.0), (0.0, 1.0)],
    },
    {
        "id": "zone_3",
        "name": "Zone D (Bottom-Right)",
        "area": 50,
        "polygon": [(0.5, 0.5), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0)],
    },
]

# Maximum number of zones user can create
MAX_ZONES = 12
MIN_ZONES = 1

# ==============================================================================
# SPATIAL EXIT POINT DEFAULTS
# ==============================================================================

# Exit points — percentage-based coordinates for resolution independence
DEFAULT_EXIT_POINTS = [
    {
        "id": "exit_0",
        "name": "Main Gate",
        "x_pct": 0.5,
        "y_pct": 0.0,
        "capacity": 20,   # people per minute
        "status": "OPEN",  # OPEN or BLOCKED
    },
    {
        "id": "exit_1",
        "name": "South Exit",
        "x_pct": 0.5,
        "y_pct": 1.0,
        "capacity": 20,
        "status": "OPEN",
    },
]

# Maximum number of exits user can configure
MAX_EXITS = 8
MIN_EXITS = 1

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
    "BLOCKED": "#FF0000"    # Red - do not use
}

EXIT_STATUS_COLORS_BGR = {
    "OPEN": (0, 255, 0),
    "BLOCKED": (0, 0, 255),
}

# ==============================================================================
# UI CONFIGURATION
# ==============================================================================

# Zone area limits (square meters)
MIN_ZONE_AREA = 10
MAX_ZONE_AREA = 500
DEFAULT_ZONE_AREA = 50

# ==============================================================================
# EMERGENCY TIMER CONFIGURATION
# ==============================================================================

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
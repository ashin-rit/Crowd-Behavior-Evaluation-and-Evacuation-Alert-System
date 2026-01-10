"""
Configuration constants for the Crowd Behavior Evaluation System.
"""

# Zone names and their assigned exits
ZONE_CONFIG = {
    0: {"name": "Zone 1 (Top-Left)", "exit": "North Exit", "short": "Zone 1"},
    1: {"name": "Zone 2 (Top-Right)", "exit": "East Exit", "short": "Zone 2"},
    2: {"name": "Zone 3 (Bottom-Left)", "exit": "West Exit", "short": "Zone 3"},
    3: {"name": "Zone 4 (Bottom-Right)", "exit": "South Exit", "short": "Zone 4"}
}

# Status thresholds (percentage of capacity)
THRESHOLDS = {
    'SAFE': 0.50,
    'WARNING': 0.85
}

# Heatmap overlay alpha values
OVERLAY_ALPHA = {
    "SAFE": 0.1,
    "WARNING": 0.2,
    "EMERGENCY": 0.3
}

# Status colors - BGR (OpenCV)
COLORS_BGR = {
    "SAFE": (0, 255, 0),        # Green
    "WARNING": (0, 255, 255),    # Yellow
    "EMERGENCY": (0, 0, 255)     # Red
}

# Status colors - RGB (Streamlit/Plotly)
COLORS_RGB = {
    "SAFE": "#00FF00",
    "WARNING": "#FFFF00",
    "EMERGENCY": "#FF0000"
}

# Audio alert URL (Royalty-free alarm)
ALARM_URL = 'https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3'

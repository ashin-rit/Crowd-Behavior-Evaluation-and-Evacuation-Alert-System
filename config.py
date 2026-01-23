"""
Configuration and constants for the Crowd Behavior Evaluation System.
"""

# Zone names and their assigned exits
ZONE_CONFIG = {
    0: {"name": "Zone 1 (Top-Left)", "exit": "North Exit", "short": "Zone 1"},
    1: {"name": "Zone 2 (Top-Right)", "exit": "East Exit", "short": "Zone 2"},
    2: {"name": "Zone 3 (Bottom-Left)", "exit": "West Exit", "short": "Zone 3"},
    3: {"name": "Zone 4 (Bottom-Right)", "exit": "South Exit", "short": "Zone 4"}
}

# Status colors in BGR format (for OpenCV)
STATUS_COLORS_BGR = {
    "SAFE": (0, 255, 0),        # Green
    "WARNING": (0, 255, 255),    # Yellow
    "EMERGENCY": (0, 0, 255)     # Red
}

# Status colors in RGB format (for Streamlit)
STATUS_COLORS_RGB = {
    "SAFE": "#00FF00",
    "WARNING": "#FFFF00",
    "EMERGENCY": "#FF0000"
}

# Overlay alpha values for heatmap
OVERLAY_ALPHA = {
    "SAFE": 0.1,
    "WARNING": 0.2,
    "EMERGENCY": 0.3
}

# Custom CSS for enhanced visuals
CUSTOM_CSS = """
<style>
    /* Main container styling */
    .main {
        padding: 1rem;
    }
    
    /* Alert box styles */
    .safe-alert {
        background: linear-gradient(135deg, #1a4d1a, #2d7d2d);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #00ff00;
        margin: 0.5rem 0;
    }
    
    .warning-alert {
        background: linear-gradient(135deg, #4d4d1a, #7d7d2d);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffff00;
        margin: 0.5rem 0;
    }
    
    .emergency-alert {
        background: linear-gradient(135deg, #4d1a1a, #7d2d2d);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ff0000;
        margin: 0.5rem 0;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Alarm banner */
    .alarm-banner {
        background: linear-gradient(90deg, #ff0000, #cc0000, #ff0000);
        color: white;
        padding: 1rem;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        border-radius: 10px;
        animation: flash 0.5s infinite;
        margin: 1rem 0;
    }
    
    @keyframes flash {
        0%, 100% { background: linear-gradient(90deg, #ff0000, #cc0000, #ff0000); }
        50% { background: linear-gradient(90deg, #cc0000, #ff0000, #cc0000); }
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e, #2d2d3d);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    /* Zone status headers */
    .zone-header {
        font-size: 1.2rem;
        font-weight: bold;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
    }
</style>
"""

"""
================================================================================
INTELLIGENT CROWD BEHAVIOR EVALUATION & EVACUATION SYSTEM
================================================================================
MCA Final Year Project
Author: Ashin Saji

Description:
    This application analyzes uploaded CCTV footage (MP4) to detect crowd density,
    classify risk levels using a "Traffic Light" system (Safe/Warning/Emergency),
    and generate real-time evacuation instructions.

Features:
    - YOLO-based person detection with bounding boxes
    - Smart Grid (2x2) zone division for localized density analysis
    - Traffic Light classification system (Green/Yellow/Red)
    - Heatmap overlays for visual density representation
    - Real-time evacuation instructions and alerts
    - Audio alarm simulation for emergency situations
================================================================================
"""

# ==============================================================================
# SECTION 1: IMPORTS AND PAGE CONFIGURATION
# ==============================================================================
import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import tempfile
import time
from PIL import Image

# Page configuration - Wide layout for dashboard-style display
st.set_page_config(
    page_title="Crowd Behavior Evaluation System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced visuals
st.markdown("""
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
""", unsafe_allow_html=True)


# ==============================================================================
# SECTION 2: YOLO MODEL LOADING WITH CACHING
# ==============================================================================
@st.cache_resource
def load_yolo_model():
    """
    Load the YOLOv8 model with caching to prevent reloading on every frame.
    
    Uses @st.cache_resource decorator to cache the model in memory.
    This is critical for performance as model loading is expensive.
    
    Returns:
        YOLO: Loaded YOLOv8 nano model for person detection
    """
    # Using YOLOv8 nano for balance between speed and accuracy
    # 'yolov8n.pt' will be auto-downloaded on first run
    model = YOLO('yolov8n.pt')
    return model


# ==============================================================================
# SECTION 3: ZONE CONFIGURATION AND CONSTANTS
# ==============================================================================

# Zone names and their assigned exits (hardcoded as per requirements)
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


# ==============================================================================
# SECTION 4: HELPER FUNCTIONS
# ==============================================================================

def get_zone(cx: int, cy: int, frame_width: int, frame_height: int) -> int:
    """
    Determine which zone (0-3) a point belongs to based on 2x2 grid division.
    
    ZONE DIVISION LOGIC (Academic Explanation):
    ============================================
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
        
    The midpoint divides the frame:
        - Horizontal midpoint: frame_width // 2
        - Vertical midpoint: frame_height // 2
        
    Zone assignment:
        - If cx < mid_x AND cy < mid_y: Zone 0 (Top-Left)
        - If cx >= mid_x AND cy < mid_y: Zone 1 (Top-Right)
        - If cx < mid_x AND cy >= mid_y: Zone 2 (Bottom-Left)
        - If cx >= mid_x AND cy >= mid_y: Zone 3 (Bottom-Right)
    
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
    
    TRAFFIC LIGHT CLASSIFICATION SYSTEM (Academic Explanation):
    ===========================================================
    The system uses a three-tier classification based on crowd density:
    
    1. SAFE (Green): Count is 0-50% of threshold
       - Normal operations, monitoring only
       - Low risk of overcrowding
       
    2. WARNING (Yellow): Count is 50-85% of threshold
       - Increased density detected
       - Proactive measures needed (slow entry, increase monitoring)
       
    3. EMERGENCY (Red): Count is >85% of threshold
       - Critical overcrowding
       - Immediate evacuation required
    
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


def draw_zone_overlay(frame: np.ndarray, zone: int, status: str, 
                      frame_width: int, frame_height: int) -> np.ndarray:
    """
    Draw a semi-transparent heatmap overlay on the specified zone.
    
    The overlay color and transparency are determined by the zone's status:
    - SAFE: Green with 10% opacity
    - WARNING: Yellow with 20% opacity
    - EMERGENCY: Red with 30% opacity
    
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
    
    HUD DESIGN (Academic Explanation):
    ==================================
    Each zone displays:
    - Zone name (e.g., "Zone 1")
    - People count (e.g., "People: 12")
    - Status indicator color
    
    The HUD text is positioned at the top-left corner of each zone
    with a semi-transparent background for readability.
    
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


def process_frame(frame: np.ndarray, model: YOLO, threshold: int) -> tuple:
    """
    Main processing function for each video frame.
    
    PROCESSING PIPELINE (Academic Explanation):
    ==========================================
    1. Run YOLO inference to detect people (class 0)
    2. For each detection, calculate center point of bounding box
    3. Assign each person to a zone based on their center point
    4. Calculate status for each zone based on count vs threshold
    5. Draw visualizations:
       - Heatmap overlays (semi-transparent zone colors)
       - Bounding boxes around detected people
       - Grid lines separating zones
       - HUD with zone names and counts
    
    Args:
        frame: Input video frame (BGR format)
        model: Loaded YOLO model
        threshold: Capacity threshold for zone classification
        
    Returns:
        tuple: (processed_frame, zone_counts, zone_statuses)
            - processed_frame: Frame with all visualizations
            - zone_counts: Dict mapping zone index to people count
            - zone_statuses: Dict mapping zone index to status string
    """
    frame_height, frame_width = frame.shape[:2]
    
    # Initialize zone counts
    zone_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    
    # Run YOLO inference
    # classes=[0] filters for 'person' class only
    results = model(frame, classes=[0], verbose=False)
    
    # Process detections
    detections = []
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Get bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            
            # Calculate center point of bounding box
            # This is used to determine which zone the person is in
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            
            # Determine zone based on center point
            zone = get_zone(cx, cy, frame_width, frame_height)
            zone_counts[zone] += 1
            
            detections.append({
                'bbox': (x1, y1, x2, y2),
                'center': (cx, cy),
                'zone': zone,
                'confidence': confidence
            })
    
    # Calculate status for each zone
    zone_statuses = {}
    for zone in range(4):
        zone_statuses[zone] = get_status(zone_counts[zone], threshold)
    
    # Draw visualizations
    # Step 1: Draw heatmap overlays for each zone
    for zone in range(4):
        frame = draw_zone_overlay(frame, zone, zone_statuses[zone], 
                                  frame_width, frame_height)
    
    # Step 2: Draw bounding boxes on detected people
    # Color is based on the zone's current status
    for detection in detections:
        x1, y1, x2, y2 = detection['bbox']
        zone = detection['zone']
        status = zone_statuses[zone]
        color = STATUS_COLORS_BGR[status]
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw confidence label
        label = f"{detection['confidence']:.2f}"
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, color, 2, cv2.LINE_AA)
    
    # Step 3: Draw grid lines
    frame = draw_zone_grid(frame, frame_width, frame_height)
    
    # Step 4: Draw HUD for each zone
    for zone in range(4):
        frame = draw_zone_hud(frame, zone, zone_counts[zone], 
                             zone_statuses[zone], frame_width, frame_height)
    
    return frame, zone_counts, zone_statuses


def generate_instructions(zone_statuses: dict, zone_counts: dict) -> list:
    """
    Generate evacuation instructions based on zone statuses.
    
    INSTRUCTION LOGIC (Academic Explanation):
    =========================================
    Instructions are generated for each zone based on its status:
    
    - SAFE: "Status Normal. Monitoring..."
    - WARNING: "High Density in [Zone]. Slow down entry."
    - EMERGENCY: "CRITICAL: EVACUATE [Zone] via [Exit]!"
    
    Exit assignments are hardcoded:
    - Zone 1 (Top-Left): North Exit
    - Zone 2 (Top-Right): East Exit
    - Zone 3 (Bottom-Left): West Exit
    - Zone 4 (Bottom-Right): South Exit
    
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


# ==============================================================================
# SECTION 5: MAIN APPLICATION UI
# ==============================================================================

def main():
    """Main application entry point."""
    
    # -------------------------------------------------------------------------
    # SIDEBAR: Control Panel
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("## 🎛️ Control Panel")
        st.markdown("---")
        
        # Video upload
        st.markdown("### 📹 Video Input")
        uploaded_file = st.file_uploader(
            "Upload CCTV Footage (MP4)",
            type=['mp4', 'avi', 'mov'],
            help="Upload a video file to analyze crowd behavior"
        )
        
        st.markdown("---")
        
        # Threshold configuration
        st.markdown("### ⚙️ Configuration")
        threshold = st.slider(
            "Capacity Threshold (per zone)",
            min_value=1,
            max_value=50,
            value=10,
            help="Maximum people per zone before triggering alerts"
        )
        
        # Display threshold breakdown
        st.markdown("#### Traffic Light Thresholds:")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"🟢 Safe: 0-{int(threshold * 0.5)}")
            st.markdown(f"🟡 Warning: {int(threshold * 0.5)+1}-{int(threshold * 0.85)}")
        with col2:
            st.markdown(f"🔴 Emergency: >{int(threshold * 0.85)}")
        
        st.markdown("---")
        
        # Processing controls
        st.markdown("### ▶️ Playback")
        frame_skip = st.slider(
            "Frame Skip",
            min_value=1,
            max_value=10,
            value=2,
            help="Process every Nth frame for faster playback"
        )
        
        st.markdown("---")
        
        # System info
        st.markdown("### 📊 System Info")
        st.info("Model: YOLOv8 Nano")
        st.info("Detection: Person (Class 0)")
    
    # -------------------------------------------------------------------------
    # MAIN AREA: Title and Layout
    # -------------------------------------------------------------------------
    st.markdown("# 🚨 Intelligent Crowd Behavior Evaluation System")
    st.markdown("##### Real-time crowd density analysis with automated evacuation alerts")
    st.markdown("---")
    
    # Create main layout: 70% video, 30% dashboard
    video_col, dashboard_col = st.columns([7, 3])
    
    # -------------------------------------------------------------------------
    # VIDEO COLUMN (70%)
    # -------------------------------------------------------------------------
    with video_col:
        st.markdown("### 📺 Live Video Feed")
        video_placeholder = st.empty()
        
        # Status bar below video
        status_bar = st.empty()
    
    # -------------------------------------------------------------------------
    # DASHBOARD COLUMN (30%)
    # -------------------------------------------------------------------------
    with dashboard_col:
        st.markdown("### 📊 Real-time Metrics")
        metrics_placeholder = st.empty()
        
        st.markdown("### 📋 Zone Status")
        zone_status_placeholder = st.empty()
        
        st.markdown("### 🚨 Live Instructions")
        instructions_placeholder = st.empty()
        
        # Alarm banner placeholder
        alarm_placeholder = st.empty()
    
    # -------------------------------------------------------------------------
    # VIDEO PROCESSING LOOP
    # -------------------------------------------------------------------------
    if uploaded_file is not None:
        # Load YOLO model (cached)
        model = load_yolo_model()
        
        # Save uploaded file to temp location
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        tfile.close()
        
        # Open video capture
        cap = cv2.VideoCapture(tfile.name)
        
        if not cap.isOpened():
            st.error("Error: Could not open video file.")
            return
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # Progress bar
        progress_bar = st.progress(0)
        
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break
            
            frame_count += 1
            
            # Skip frames for performance
            if frame_count % frame_skip != 0:
                continue
            
            # Process frame
            processed_frame, zone_counts, zone_statuses = process_frame(
                frame, model, threshold
            )
            
            # Convert BGR to RGB for display
            processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            
            # Display video frame
            video_placeholder.image(processed_frame_rgb, channels="RGB", 
                                   use_container_width=True)
            
            # Update progress
            progress = frame_count / total_frames
            progress_bar.progress(min(progress, 1.0))
            
            # Generate instructions
            instructions = generate_instructions(zone_statuses, zone_counts)
            
            # Check for emergency status
            has_emergency = any(s == "EMERGENCY" for s in zone_statuses.values())
            
            # Update metrics display
            with metrics_placeholder.container():
                # Create bar chart data
                chart_data = {
                    'Zone': ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4'],
                    'People': [zone_counts[0], zone_counts[1], 
                              zone_counts[2], zone_counts[3]]
                }
                st.bar_chart(chart_data, x='Zone', y='People', 
                            color='#00ff00', height=200)
            
            # Update zone status display
            with zone_status_placeholder.container():
                cols = st.columns(2)
                for i, zone in enumerate(range(4)):
                    with cols[i % 2]:
                        status = zone_statuses[zone]
                        color = STATUS_COLORS_RGB[status]
                        count = zone_counts[zone]
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #1e1e2e, #2d2d3d); 
                                    padding: 0.5rem; border-radius: 8px; 
                                    border-left: 4px solid {color}; margin: 0.25rem 0;">
                            <strong style="color: {color};">{ZONE_CONFIG[zone]['short']}</strong><br>
                            <span style="color: white;">👥 {count} people</span><br>
                            <span style="color: {color};">{status}</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Update instructions display
            with instructions_placeholder.container():
                for instr in instructions:
                    status = instr['status']
                    if status == "SAFE":
                        st.markdown(f"""
                        <div class="safe-alert">
                            {instr['message']}
                        </div>
                        """, unsafe_allow_html=True)
                    elif status == "WARNING":
                        st.markdown(f"""
                        <div class="warning-alert">
                            {instr['message']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="emergency-alert">
                            {instr['message']}
                        </div>
                        """, unsafe_allow_html=True)
            
            # Show alarm banner if emergency
            if has_emergency:
                alarm_placeholder.markdown("""
                <div class="alarm-banner">
                    🔊 AUDIO ALARM TRIGGERED 🔊
                </div>
                """, unsafe_allow_html=True)
            else:
                alarm_placeholder.empty()
            
            # Update status bar
            total_people = sum(zone_counts.values())
            status_bar.markdown(f"""
            **Frame:** {frame_count}/{total_frames} | 
            **Total People:** {total_people} | 
            **FPS:** {fps} | 
            **Threshold:** {threshold}
            """)
            
            # Small delay for smooth playback
            time.sleep(0.01)
        
        cap.release()
        progress_bar.progress(1.0)
        
        st.success("✅ Video processing complete!")
        
    else:
        # Display placeholder when no video is uploaded
        with video_col:
            video_placeholder.markdown("""
            <div style="background: linear-gradient(135deg, #1e1e2e, #2d2d3d);
                        border: 2px dashed #4a4a5a; border-radius: 10px;
                        height: 400px; display: flex; align-items: center;
                        justify-content: center; flex-direction: column;">
                <span style="font-size: 4rem;">📹</span>
                <h3 style="color: #8a8a9a;">Upload a video to begin analysis</h3>
                <p style="color: #6a6a7a;">Supported formats: MP4, AVI, MOV</p>
            </div>
            """, unsafe_allow_html=True)
        
        with dashboard_col:
            metrics_placeholder.info("📊 Metrics will appear here during analysis")
            zone_status_placeholder.info("📋 Zone status will update in real-time")
            instructions_placeholder.info("🚨 Evacuation instructions will appear here")


# ==============================================================================
# SECTION 6: ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    main()

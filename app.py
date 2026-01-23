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
import tempfile
import time
from PIL import Image

# Import custom modules
import config
from config import ZONE_CONFIG, STATUS_COLORS_RGB, CUSTOM_CSS
from model_loader import load_yolo_model
from processor import process_frame
from logic import generate_instructions

# Page configuration - Wide layout for dashboard-style display
st.set_page_config(
    page_title="Crowd Behavior Evaluation System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced visuals
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# SECTION 2: MAIN APPLICATION UI
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
            
            # Process frame using the processor module
            processed_frame, zone_counts, zone_statuses = process_frame(
                frame, model, threshold
            )
            
            # Convert BGR to RGB for display
            processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            
            # Display video frame (FIXED: use width="stretch" instead of use_container_width)
            video_placeholder.image(processed_frame_rgb, channels="RGB", 
                                   width="stretch")
            
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
        # FIXED: applied user's CSS fix for justify-content and flex-direction
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


if __name__ == "__main__":
    main()
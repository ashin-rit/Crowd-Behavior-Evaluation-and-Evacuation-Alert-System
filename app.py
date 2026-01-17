"""
================================================================================
INTELLIGENT CROWD BEHAVIOR EVALUATION & EVACUATION SYSTEM - v2.0 (ADVANCED)
================================================================================
MCA Final Year Project
Author: Ashin Saji

Advanced Features: Batch Processing, Tracking, Analytics, and Audio Alerts.
"""

import streamlit as st
import cv2
import numpy as np
<<<<<<< HEAD
=======
import os
>>>>>>> 354d7719701288fca6cc20a7710001c53e771c4e
import tempfile
import time
import plotly.graph_objects as go
from ultralytics import YOLO
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime

<<<<<<< HEAD
# Import custom modules
import config
from config import ZONE_CONFIG, STATUS_COLORS_RGB, CUSTOM_CSS
from model_loader import load_yolo_model
from processor import process_frame
from logic import generate_instructions

# Page configuration - Wide layout for dashboard-style display
=======
# Import configuration constants
import config

# ==============================================================================
# SECTION 1: PAGE CONFIGURATION & SESSION STATE
# ==============================================================================
>>>>>>> 354d7719701288fca6cc20a7710001c53e771c4e
st.set_page_config(
    page_title="Crowd Evaluation System v2.0",
    page_icon="🚨",
    layout="wide"
)

<<<<<<< HEAD
# Custom CSS for enhanced visuals
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
=======
# Custom CSS
st.markdown("""
<style>
    .emergency-banner {
        background-color: #ff0000;
        color: white;
        padding: 15px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        border-radius: 10px;
        animation: blinker 0.8s linear infinite;
        margin-bottom: 20px;
    }
    @keyframes blinker {
        50% { opacity: 0.1; }
    }
    .status-card {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 5px solid;
    }
</style>
""", unsafe_allow_html=True)
>>>>>>> 354d7719701288fca6cc20a7710001c53e771c4e

# Initialize Session State
if 'history' not in st.session_state:
    st.session_state.history = {'timestamps': [], 'zone_counts': []}
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'stop_requested' not in st.session_state:
    st.session_state.stop_requested = False
if 'alarm_playing' not in st.session_state:
    st.session_state.alarm_playing = False

# ==============================================================================
<<<<<<< HEAD
# SECTION 2: MAIN APPLICATION UI
=======
# SECTION 2: CORE LOGIC FUNCTIONS
# ==============================================================================

@st.cache_resource
def load_yolo_model(model_name):
    """Load and cache the YOLO model."""
    try:
        return YOLO(model_name)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

def get_zone(x, y, w, h):
    """Identify zone index for a point."""
    mid_x, mid_y = w // 2, h // 2
    if x < mid_x:
        return 0 if y < mid_y else 2
    else:
        return 1 if y < mid_y else 3

def get_zones_occupied(x1, y1, x2, y2, w, h):
    """Detect all zones touched by a bounding box."""
    corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2), ((x1+x2)//2, (y1+y2)//2)]
    zones = set()
    for cx, cy in corners:
        zones.add(get_zone(cx, cy, w, h))
    return list(zones)

def calculate_dynamic_thresholds(base_threshold, w, h):
    """Calculate thresholds adjusted for zone area variations."""
    mid_x, mid_y = w // 2, h // 2
    areas = {
        0: mid_x * mid_y,
        1: (w - mid_x) * mid_y,
        2: mid_x * (h - mid_y),
        3: (w - mid_x) * (h - mid_y)
    }
    avg_area = (w * h) / 4
    return {z: int(base_threshold * (a / avg_area)) for z, a in areas.items()}

def get_status(count, threshold):
    """Three-level classification logic."""
    if threshold <= 0: return "SAFE"
    ratio = count / threshold
    if ratio <= config.THRESHOLDS['SAFE']: return "SAFE"
    if ratio <= config.THRESHOLDS['WARNING']: return "WARNING"
    return "EMERGENCY"

# ==============================================================================
# SECTION 3: VISUALIZATION HELPERS
# ==============================================================================

def draw_overlays(frame, results, zone_counts, zone_statuses, thresholds):
    """Render all visualizations on the frame."""
    h, w = frame.shape[:2]
    mid_x, mid_y = w // 2, h // 2
    
    # 1. Heatmap Zones
    for z, status in zone_statuses.items():
        overlay = frame.copy()
        color = config.COLORS_BGR[status]
        alpha = config.OVERLAY_ALPHA[status]
        
        # Define zone rect
        coords = [
            (0, 0, mid_x, mid_y), (mid_x, 0, w, mid_y),
            (0, mid_y, mid_x, h), (mid_x, mid_y, w, h)
        ][z]
        cv2.rectangle(overlay, (coords[0], coords[1]), (coords[2], coords[3]), color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    # 2. Detections/Tracking
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            # Determine primary zone for bounding box color
            z_primary = get_zone((x1+x2)//2, (y1+y2)//2, w, h)
            color = config.COLORS_BGR[zone_statuses[z_primary]]
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Label (ID + Conf if available)
            label = f"#{int(box.id[0]) if box.id is not None else ''} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # 3. Grid Lines
    cv2.line(frame, (mid_x, 0), (mid_x, h), (255, 255, 255), 1)
    cv2.line(frame, (0, mid_y), (w, mid_y), (255, 255, 255), 1)
    
    # 4. HUD
    for z, count in zone_counts.items():
        coords = [(10, 30), (mid_x + 10, 30), (10, mid_y + 30), (mid_x + 10, mid_y + 30)][z]
        status = zone_statuses[z]
        cv2.putText(frame, f"{config.ZONE_CONFIG[z]['short']}: {int(count)}", 
                    coords, cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.COLORS_BGR[status], 2)

    return frame

# ==============================================================================
# SECTION 4: MAIN UI & WORKFLOW
>>>>>>> 354d7719701288fca6cc20a7710001c53e771c4e
# ==============================================================================

def main():
    # Sidebar
    st.sidebar.title("🎛️ Control Panel")
    
    video_file = st.sidebar.file_uploader("Upload CCTV Video", type=['mp4', 'avi', 'mov'])
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Detection Settings")
    model_choice = st.sidebar.selectbox("YOLO Model", ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"])
    conf_thresh = st.sidebar.slider("Confidence Threshold", 0.1, 1.0, 0.4)
    base_thresh = st.sidebar.slider("Target Capacity (per zone)", 1, 100, 20)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Processing")
    batch_size = st.sidebar.select_slider("Buffer Multiplier (Batch)", options=[1, 4, 8, 16], value=4)
    enable_tracking = st.sidebar.checkbox("Enable ByteTrack", value=True)
    export_video = st.sidebar.checkbox("Generate Downloadable Output", value=False)

    # Action Buttons
    col_play, col_stop = st.sidebar.columns(2)
    if col_play.button("▶️ Start / Resume"):
        st.session_state.processing = True
        st.session_state.stop_requested = False
    if col_stop.button("⏹️ Stop"):
        st.session_state.processing = False
        st.session_state.stop_requested = True

    # Header
    st.title("🚨 Intelligent Crowd Behavior System v2.0")
    st.info("Advanced Real-time Analytics & Evacuation Management")

    if video_file:
        # Load Model
        model = load_yolo_model(model_choice)
        
        # Handle Temp File
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(video_file.read())
        tfile.close()
        
        try:
            cap = cv2.VideoCapture(tfile.name)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Dynamic Thresholds
            zone_thresholds = calculate_dynamic_thresholds(base_thresh, w, h)
            
            # UI Placeholders
            main_col, side_col = st.columns([2, 1])
            with main_col:
                video_placeholder = st.empty()
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            with side_col:
                st.subheader("📊 Live Metrics")
                chart_placeholder = st.empty()
                alert_placeholder = st.empty()
                alarm_banner = st.empty()

            # Video Writer for Export
            out_writer = None
            if export_video:
                export_path = os.path.join(tempfile.gettempdir(), f"processed_{video_file.name}")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out_writer = cv2.VideoWriter(export_path, fourcc, fps, (w, h))

            frame_buffer = []
            processed_count = 0
            
<<<<<<< HEAD
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
=======
            while cap.isOpened() and not st.session_state.stop_requested:
                if not st.session_state.processing:
                    time.sleep(0.5)
                    continue

                ret, frame = cap.read()
                if not ret: break
                
                frame_buffer.append(frame)
                
                if len(frame_buffer) >= batch_size:
                    # BATCH INFERENCE
                    if enable_tracking:
                        # Tracking doesn't support batching in simple way, iterate
                        results = [model.track(f, conf=conf_thresh, persist=True, classes=[0], verbose=False)[0] for f in frame_buffer]
>>>>>>> 354d7719701288fca6cc20a7710001c53e771c4e
                    else:
                        results = model(frame_buffer, conf=conf_thresh, classes=[0], verbose=False)
                    
                    for i, (f, res) in enumerate(zip(frame_buffer, results)):
                        # Zone Counting Logic
                        zone_counts = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
                        for box in res.boxes:
                            x1, y1, x2, y2 = box.xyxy[0]
                            zones = get_zones_occupied(int(x1), int(y1), int(x2), int(y2), w, h)
                            for z in zones:
                                zone_counts[z] += (1.0 / len(zones))
                        
                        # Determine Status
                        zone_statuses = {z: get_status(zone_counts[z], zone_thresholds[z]) for z in range(4)}
                        
                        # Optimization: Only update UI for the last frame in buffer to keep UI snappy
                        # But ALWAYS write all frames to file if exporting
                        processed_frame = draw_overlays(f.copy(), [res], zone_counts, zone_statuses, zone_thresholds)
                        
                        if export_video:
                            out_writer.write(processed_frame)

                        if i == len(frame_buffer) - 1:
                            # Update Visuals
                            video_placeholder.image(processed_frame, channels="BGR", width="stretch")
                            
                            # History Recording
                            st.session_state.history['timestamps'].append(processed_count)
                            st.session_state.history['zone_counts'].append(list(zone_counts.values()))
                            
                            # Alerts & Alarm
                            has_emergency = any(s == "EMERGENCY" for s in zone_statuses.values())
                            if has_emergency:
                                alarm_banner.markdown('<div class="emergency-banner">🔊 CRITICAL EVACUATION REQUIRED</div>', unsafe_allow_html=True)
                                if not st.session_state.alarm_playing:
                                    streamlit_js_eval(js_expressions=f"new Audio('{config.ALARM_URL}').play();", key=f"alarm_{processed_count}")
                                    st.session_state.alarm_playing = True
                            else:
                                alarm_banner.empty()
                                st.session_state.alarm_playing = False
                            
                            with alert_placeholder.container():
                                for z, status in zone_statuses.items():
                                    bgcolor = config.COLORS_RGB[status]
                                    txt_color = "black" if status == "WARNING" else "white"
                                    msg = config.ZONE_CONFIG[z]['name'] + ": "
                                    if status == "SAFE": msg += "Monitoring..."
                                    elif status == "WARNING": msg += "Increase Surveillance"
                                    else: msg += f"EVACUATE via {config.ZONE_CONFIG[z]['exit']}"
                                    
                                    st.markdown(f'<div class="status-card" style="background-color: {bgcolor}; color: {txt_color};">{msg}</div>', unsafe_allow_html=True)

                            # Plotly Chart
                            fig = go.Figure()
                            for z in range(4):
                                fig.add_trace(go.Scatter(y=[h[z] for h in st.session_state.history['zone_counts'][-50:]], 
                                                        mode='lines', name=config.ZONE_CONFIG[z]['short'], line=dict(color=config.COLORS_RGB['SAFE'] if z==0 else None)))
                            fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), legend=dict(orientation="h"))
                            chart_placeholder.plotly_chart(fig, width="stretch", key=f"plotly_{processed_count}")

                        processed_count += 1
                    
                    # Update Progress
                    progress_bar.progress(min(processed_count / total_frames, 1.0))
                    status_text.text(f"Processed: {processed_count} / {total_frames} frames (Batch Size: {batch_size})")
                    frame_buffer = []

            # Cleanup & Export
            cap.release()
            if out_writer: out_writer.release()
            
            if export_video and os.path.exists(export_path):
                with open(export_path, 'rb') as f:
                    st.sidebar.download_button("📥 Download Result", f, file_name="analysis_output.mp4")

        except Exception as e:
            st.error(f"Processing Failure: {e}")
        finally:
            if 'cap' in locals(): cap.release()
            try: os.unlink(tfile.name)
            except: pass

    else:
<<<<<<< HEAD
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


=======
        st.info("Please upload a video file to proceed.")

>>>>>>> 354d7719701288fca6cc20a7710001c53e771c4e
if __name__ == "__main__":
    main()
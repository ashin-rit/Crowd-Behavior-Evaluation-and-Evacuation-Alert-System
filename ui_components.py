"""
================================================================================
UI COMPONENTS MODULE
================================================================================
Streamlit UI components for sidebar configuration and dashboard panels.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

import streamlit as st
from typing import Dict, List, Tuple

from config import (
    DEFAULT_ZONE_CONFIG, DEFAULT_EXIT_CONFIG, DEFAULT_NUM_EXITS,
    MIN_EXITS, MAX_EXITS, MIN_ZONE_AREA, MAX_ZONE_AREA, DEFAULT_ZONE_AREA,
    EXIT_DIRECTIONS, STATUS_COLORS_HEX, EXIT_STATUS_COLORS
)


def render_sidebar_config() -> Tuple[Dict, List[Dict], int]:
    """
    Render the sidebar configuration panel.
    
    Returns:
        tuple: (zone_config, exit_config, frame_skip)
    """
    st.sidebar.markdown("## 🎛️ Control Panel")
    st.sidebar.markdown("---")
    
    # Video upload
    st.sidebar.markdown("### 📹 Video Input")
    uploaded_file = st.sidebar.file_uploader(
        "Upload CCTV Footage",
        type=['mp4', 'avi', 'mov'],
        help="Upload a video file to analyze crowd behavior"
    )
    
    st.sidebar.markdown("---")
    
    # Zone Configuration
    st.sidebar.markdown("### 📐 Zone Configuration")
    use_default_zones = st.sidebar.checkbox("Use Default Zone Areas", value=True)
    
    if use_default_zones:
        zone_config = DEFAULT_ZONE_CONFIG.copy()
    else:
        zone_config = {}
        cols = st.sidebar.columns(2)
        for i in range(4):
            with cols[i % 2]:
                area = st.number_input(
                    f"Zone {i+1} (m²)",
                    min_value=MIN_ZONE_AREA,
                    max_value=MAX_ZONE_AREA,
                    value=DEFAULT_ZONE_AREA,
                    key=f"zone_{i}_area"
                )
                zone_config[i] = {
                    **DEFAULT_ZONE_CONFIG[i],
                    "area": area
                }
    
    st.sidebar.markdown("---")
    
    # Exit Configuration
    st.sidebar.markdown("### 🚪 Exit Configuration")
    
    num_exits = st.sidebar.slider(
        "Number of Exits",
        min_value=MIN_EXITS,
        max_value=MAX_EXITS,
        value=DEFAULT_NUM_EXITS,
        help="Configure the number of exits in the venue"
    )
    
    exit_config = []
    
    for i in range(num_exits):
        with st.sidebar.expander(f"Exit {i+1}", expanded=(i < 2)):
            # Get defaults if available
            default = DEFAULT_EXIT_CONFIG[i] if i < len(DEFAULT_EXIT_CONFIG) else {
                "name": f"Exit {i+1}",
                "direction": EXIT_DIRECTIONS[i % len(EXIT_DIRECTIONS)],
                "zones": [i % 4]
            }
            
            name = st.text_input(
                "Exit Name",
                value=default.get("name", f"Exit {i+1}"),
                key=f"exit_{i}_name"
            )
            
            direction = st.selectbox(
                "Direction",
                options=EXIT_DIRECTIONS,
                index=EXIT_DIRECTIONS.index(default.get("direction", "North")) if default.get("direction") in EXIT_DIRECTIONS else 0,
                key=f"exit_{i}_dir"
            )
            
            # Zone selection (1-indexed for user, 0-indexed internally)
            default_zones = [z + 1 for z in default.get("zones", [0])]
            zones = st.multiselect(
                "Associated Zones",
                options=[1, 2, 3, 4],
                default=default_zones,
                key=f"exit_{i}_zones",
                help="Select which zones can use this exit"
            )
            
            exit_config.append({
                "id": f"exit_{i}",
                "name": name,
                "direction": direction,
                "zones": [z - 1 for z in zones]  # Convert to 0-indexed
            })
    
    st.sidebar.markdown("---")
    
    # Playback settings
    st.sidebar.markdown("### ▶️ Playback")
    frame_skip = st.sidebar.slider(
        "Frame Skip",
        min_value=1,
        max_value=10,
        value=2,
        help="Process every Nth frame for faster playback"
    )
    
    st.sidebar.markdown("---")
    
    # System info
    st.sidebar.markdown("### 📊 System Info")
    st.sidebar.info("Model: YOLOv8 Nano")
    st.sidebar.info("Detection: Person (Class 0)")
    st.sidebar.info("Classification: Density-based (4 levels)")
    
    return uploaded_file, zone_config, exit_config, frame_skip


def render_zone_status_panel(placeholder, zone_counts: Dict, zone_densities: Dict,
                              zone_statuses: Dict, zone_config: Dict):
    """
    Render the zone status cards in the dashboard.
    """
    with placeholder.container():
        cols = st.columns(2)
        for i, zone in enumerate(range(4)):
            with cols[i % 2]:
                status = zone_statuses.get(zone, "SAFE")
                color = STATUS_COLORS_HEX.get(status, "#00FF00")
                count = zone_counts.get(zone, 0)
                density = zone_densities.get(zone, 0.0)
                zone_name = zone_config.get(zone, {}).get("short", f"Zone {zone + 1}")
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e1e2e, #2d2d3d); 
                            padding: 0.75rem; border-radius: 8px; 
                            border-left: 4px solid {color}; margin: 0.25rem 0;">
                    <strong style="color: {color};">{zone_name}</strong><br>
                    <span style="color: white;">👥 {count} people</span><br>
                    <span style="color: #aaa;">📊 {density:.2f}/m²</span><br>
                    <span style="color: {color}; font-size: 0.9em;">{status}</span>
                </div>
                """, unsafe_allow_html=True)


def render_exit_status_panel(placeholder, exit_config: List[Dict], exit_statuses: Dict):
    """
    Render the exit status panel in the dashboard.
    """
    with placeholder.container():
        if not exit_config:
            st.info("No exits configured")
            return
            
        cols = st.columns(min(len(exit_config), 4))
        for i, exit_info in enumerate(exit_config):
            with cols[i % len(cols)]:
                status = exit_statuses.get(i, "OPEN")
                color = EXIT_STATUS_COLORS.get(status, "#00FF00")
                name = exit_info.get("name", f"Exit {i+1}")
                direction = exit_info.get("direction", "")
                
                # Status emoji
                emoji = "🟢" if status == "OPEN" else "🟡" if status == "CROWDED" else "🔴"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e1e2e, #2d2d3d); 
                            padding: 0.5rem; border-radius: 8px; 
                            border-top: 3px solid {color}; text-align: center;">
                    <strong style="color: white;">{name}</strong><br>
                    <span style="color: #aaa; font-size: 0.8em;">{direction}</span><br>
                    <span style="font-size: 1.2em;">{emoji} {status}</span>
                </div>
                """, unsafe_allow_html=True)


def render_instructions_panel(placeholder, instructions: List[Dict]):
    """
    Render the evacuation instructions panel.
    """
    with placeholder.container():
        for instr in instructions:
            status = instr.get("status", "SAFE")
            message = instr.get("message", "")
            
            if status == "SAFE":
                css_class = "safe-alert"
            elif status == "MODERATE":
                css_class = "moderate-alert"
            elif status == "WARNING":
                css_class = "warning-alert"
            else:
                css_class = "emergency-alert"
            
            st.markdown(f"""
            <div class="{css_class}">
                {message}
            </div>
            """, unsafe_allow_html=True)


def render_metrics_panel(placeholder, zone_counts: Dict):
    """
    Render the metrics bar chart.
    """
    with placeholder.container():
        chart_data = {
            'Zone': ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4'],
            'People': [zone_counts.get(0, 0), zone_counts.get(1, 0),
                      zone_counts.get(2, 0), zone_counts.get(3, 0)]
        }
        st.bar_chart(chart_data, x='Zone', y='People', 
                    color='#00ff00', height=180)


def render_alarm_banner(placeholder, has_emergency: bool):
    """
    Render the emergency alarm banner.
    """
    if has_emergency:
        placeholder.markdown("""
        <div class="alarm-banner">
            🔊 EMERGENCY EVACUATION IN PROGRESS 🔊
        </div>
        """, unsafe_allow_html=True)
    else:
        placeholder.empty()


def get_custom_css() -> str:
    """
    Return custom CSS for the application.
    """
    return """
    <style>
        /* Main container styling */
        .main {
            padding: 1rem;
        }
        
        /* Alert box styles */
        .safe-alert {
            background: linear-gradient(135deg, #1a4d1a, #2d7d2d);
            padding: 0.75rem;
            border-radius: 8px;
            border-left: 4px solid #00ff00;
            margin: 0.3rem 0;
            color: white;
        }
        
        .moderate-alert {
            background: linear-gradient(135deg, #1a3d4d, #2d5d7d);
            padding: 0.75rem;
            border-radius: 8px;
            border-left: 4px solid #00bfff;
            margin: 0.3rem 0;
            color: white;
        }
        
        .warning-alert {
            background: linear-gradient(135deg, #4d4d1a, #7d7d2d);
            padding: 0.75rem;
            border-radius: 8px;
            border-left: 4px solid #ffff00;
            margin: 0.3rem 0;
            color: white;
        }
        
        .emergency-alert {
            background: linear-gradient(135deg, #4d1a1a, #7d2d2d);
            padding: 0.75rem;
            border-radius: 8px;
            border-left: 4px solid #ff0000;
            margin: 0.3rem 0;
            animation: pulse 1s infinite;
            color: white;
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
            font-size: 1.3rem;
            font-weight: bold;
            border-radius: 8px;
            animation: flash 0.5s infinite;
            margin: 0.5rem 0;
        }
        
        @keyframes flash {
            0%, 100% { background: linear-gradient(90deg, #ff0000, #cc0000, #ff0000); }
            50% { background: linear-gradient(90deg, #cc0000, #ff0000, #cc0000); }
        }
    </style>
    """

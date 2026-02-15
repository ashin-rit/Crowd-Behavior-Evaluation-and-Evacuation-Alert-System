"""
================================================================================
UI COMPONENTS MODULE — POLYGON ZONES & SPATIAL EXITS
================================================================================
Streamlit UI components for sidebar configuration and dashboard panels.
Updated for dynamic polygon zones and spatial exit points.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

import streamlit as st
from typing import Dict, List, Tuple

from config import (
    DEFAULT_POLYGON_ZONES, DEFAULT_EXIT_POINTS,
    MIN_ZONE_AREA, MAX_ZONE_AREA, DEFAULT_ZONE_AREA,
    STATUS_COLORS_HEX, EXIT_STATUS_COLORS
)


def render_sidebar_config() -> Tuple:
    """
    Render the sidebar configuration panel.

    Returns:
        tuple: (uploaded_file, polygon_zones, exit_points, frame_skip)
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

    # Zone info
    st.sidebar.markdown("### 📐 Detection Zones")
    polygon_zones = st.session_state.get('polygon_zones', [])
    for zone in polygon_zones:
        name = zone.get("name", zone["id"])
        area = zone.get("area", DEFAULT_ZONE_AREA)
        st.sidebar.markdown(
            f"**{name}** — {area} m² • {len(zone['polygon'])} vertices"
        )

    st.sidebar.markdown("---")

    # Exit info
    st.sidebar.markdown("### 🚪 Exit Points")
    exit_points = st.session_state.get('exit_points', [])
    for ep in exit_points:
        status = ep.get("status", "OPEN")
        emoji = "🟢" if status == "OPEN" else "🔴"
        st.sidebar.markdown(
            f"{emoji} **{ep['name']}** — {ep.get('capacity', 20)}/min"
        )

    st.sidebar.markdown("---")

    # Playback settings
    st.sidebar.markdown("### ▶️ Playback")
    frame_skip = st.sidebar.slider(
        "Frame Skip",
        min_value=1,
        max_value=10,
        value=st.session_state.get('frame_skip', 2),
        help="Process every Nth frame for faster playback"
    )

    st.sidebar.markdown("---")

    # System info
    st.sidebar.markdown("### 📊 System Info")
    st.sidebar.info("Model: YOLOv8 Nano")
    st.sidebar.info("Detection: Person (Class 0)")
    st.sidebar.info(f"Zones: {len(polygon_zones)} configured")
    st.sidebar.info(f"Exits: {len(exit_points)} configured")

    return uploaded_file, polygon_zones, exit_points, frame_skip


def render_zone_status_panel(placeholder, zone_counts: Dict, zone_densities: Dict,
                              zone_statuses: Dict, polygon_zones: List[Dict]):
    """
    Render the zone status cards in the dashboard.
    Works with dynamic polygon zone list.
    """
    with placeholder.container():
        cols = st.columns(min(len(polygon_zones), 2))
        for i, zone in enumerate(polygon_zones):
            zid = zone["id"]
            with cols[i % len(cols)]:
                status = zone_statuses.get(zid, "SAFE")
                color = STATUS_COLORS_HEX.get(status, "#00FF00")
                count = zone_counts.get(zid, 0)
                density = zone_densities.get(zid, 0.0)
                zone_name = zone.get("name", zid)

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


def render_exit_status_panel(placeholder, exit_points: List[Dict], exit_statuses: Dict):
    """
    Render the exit status panel in the dashboard.
    Works with spatial exit points.
    """
    with placeholder.container():
        if not exit_points:
            st.info("No exits configured")
            return

        cols = st.columns(min(len(exit_points), 4))
        for i, ep in enumerate(exit_points):
            with cols[i % len(cols)]:
                status = exit_statuses.get(ep["id"], "OPEN")
                color = EXIT_STATUS_COLORS.get(status, "#00FF00")
                name = ep.get("name", f"Exit {i+1}")
                capacity = ep.get("capacity", 20)

                emoji = "🟢" if status == "OPEN" else "🔴"

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e1e2e, #2d2d3d);
                            padding: 0.5rem; border-radius: 8px;
                            border-top: 3px solid {color}; text-align: center;">
                    <strong style="color: white;">{name}</strong><br>
                    <span style="color: #aaa; font-size: 0.8em;">{capacity}/min</span><br>
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


def render_metrics_panel(placeholder, zone_counts: Dict, polygon_zones: List[Dict]):
    """
    Render the metrics bar chart for dynamic zones.
    """
    with placeholder.container():
        names = [z.get("name", z["id"]) for z in polygon_zones]
        counts = [zone_counts.get(z["id"], 0) for z in polygon_zones]

        chart_data = {
            'Zone': names,
            'People': counts
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

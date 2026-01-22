"""
================================================================================
LIVE ANALYSIS PAGE (REDESIGNED + BACKEND INTEGRATED)
================================================================================
Real-time crowd monitoring with YOLO detection, zone analysis,
exit status, evacuation instructions, and audio alerts.

Author: Ashin Saji
================================================================================
"""

import streamlit as st
import cv2
import numpy as np
import tempfile
import os
import sys
import time
from datetime import datetime

# Add parent dir to path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import load_yolo_model
from visualization import process_frame, draw_zone_grid, draw_zone_overlay, draw_bounding_boxes
from zone_logic import get_zone_boundaries, calculate_density, get_status_by_density
from exit_logic import get_zone_exit_mapping, get_exit_status, get_best_exit_for_zone
from evacuation import generate_evacuation_instructions, get_global_alert_level, get_summary_message
from audio_alerts import get_audio_system
from timer_manager import EmergencyTimerManager
from config import DEFAULT_ZONE_CONFIG, DEFAULT_EXIT_CONFIG, DENSITY_THRESHOLDS


def _get_status_class(status):
    """Map status string to CSS class name."""
    return {
        "SAFE": "status-safe",
        "MODERATE": "status-moderate",
        "WARNING": "status-warning",
        "EMERGENCY": "status-emergency"
    }.get(status, "status-safe")


def _get_trend_arrow(current, previous):
    """Return trend arrow and color based on count change."""
    if previous is None:
        return "→", "var(--text-tertiary)"
    if current > previous:
        return "↑", "var(--status-warning)"
    elif current < previous:
        return "↓", "var(--status-success)"
    return "→", "var(--text-tertiary)"


def _get_exit_icon(status):
    """Return exit status icon HTML."""
    if status == "OPEN":
        return '<i class="ph-fill ph-check-circle" style="color: var(--status-success);"></i>'
    elif status == "CROWDED":
        return '<i class="ph-fill ph-warning" style="color: var(--status-warning);"></i>'
    elif status == "BLOCKED":
        return '<i class="ph-fill ph-warning-octagon" style="color: var(--status-danger);"></i>'
    return '<i class="ph-fill ph-circle" style="color: var(--text-tertiary);"></i>'


def _get_exit_border_color(status):
    """Return border color for exit status."""
    return {
        "OPEN": "var(--status-success)",
        "CROWDED": "var(--status-warning)",
        "BLOCKED": "var(--status-danger)"
    }.get(status, "var(--border-color)")


def _build_zone_card_html(zone_idx, zone_name, status, count, density, trend_arrow, trend_color):
    """Build HTML for a single zone status card."""
    status_class = _get_status_class(status)
    border_color = {
        "SAFE": "var(--status-success)",
        "MODERATE": "var(--status-moderate)",
        "WARNING": "var(--status-warning)",
        "EMERGENCY": "var(--status-danger)"
    }.get(status, "var(--border-color)")

    return (
        f'<div class="glass-card" style="border-left: 4px solid {border_color};">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">'
        f'<strong style="color: var(--text-primary); font-size: 1.125rem;">{zone_name}</strong>'
        f'<span class="status-badge {status_class}">{status}</span></div>'
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem;">'
        f'<div><p style="color: var(--text-tertiary); font-size: 0.8125rem; margin-bottom: 0.25rem;">Count</p>'
        f'<p style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;">{count}</p></div>'
        f'<div><p style="color: var(--text-tertiary); font-size: 0.8125rem; margin-bottom: 0.25rem;">Density</p>'
        f'<p style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;">{density:.2f}</p></div>'
        f'<div><p style="color: var(--text-tertiary); font-size: 0.8125rem; margin-bottom: 0.25rem;">Trend</p>'
        f'<p style="color: {trend_color}; font-size: 1.25rem; font-weight: 600;">{trend_arrow}</p></div>'
        f'</div></div>'
    )


def render():
    """Render the redesigned live analysis page"""

    # Page Header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 2.25rem; margin-bottom: 0.5rem; font-family: 'Space Grotesk', sans-serif;">
            <i class="ph-duotone ph-chart-line-up" style="color: var(--secondary-blue);"></i> <span class="gradient-text">Live Analysis</span>
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.0625rem;">
            Real-time crowd behavior monitoring and threat assessment
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Check if video is available
    has_video = 'video_file' in st.session_state and st.session_state.video_file is not None

    if not has_video:
        st.markdown("""
        <div class="glass-card glow-cyan" style="text-align: center; padding: 3rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem; color: var(--text-tertiary);"><i class="ph-duotone ph-video-camera"></i></div>
            <h2 style="color: var(--text-primary); font-family: 'Space Grotesk', sans-serif;
                       margin-bottom: 1rem;">No Video Configured</h2>
            <p style="color: var(--text-secondary); font-size: 1.0625rem; margin-bottom: 2rem;">
                Please upload a video and save configuration before starting analysis.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Go to Configuration", use_container_width=True, type="primary"):
            st.session_state.current_page = 'config'
            st.rerun()
        return

    # Initialize analysis state
    if 'analysis_running' not in st.session_state:
        st.session_state.analysis_running = False
    if 'analysis_paused' not in st.session_state:
        st.session_state.analysis_paused = False
    if 'prev_zone_counts' not in st.session_state:
        st.session_state.prev_zone_counts = None
    if 'session_data' not in st.session_state:
        st.session_state.session_data = []
    if 'analysis_frame_count' not in st.session_state:
        st.session_state.analysis_frame_count = 0

    # Control Panel
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        start_clicked = st.button("Start", use_container_width=True, type="primary")
    with col2:
        pause_clicked = st.button("Pause", use_container_width=True)
    with col3:
        stop_clicked = st.button("Stop", use_container_width=True)
    with col4:
        snapshot_clicked = st.button("Snapshot", use_container_width=True)

    if start_clicked:
        st.session_state.analysis_running = True
        st.session_state.analysis_paused = False
    if pause_clicked:
        st.session_state.analysis_paused = True
    if stop_clicked:
        st.session_state.analysis_running = False
        st.session_state.analysis_paused = False

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Layout
    col_video, col_stats = st.columns([2, 1])

    with col_video:
        video_placeholder = st.empty()
        st.markdown("<br>", unsafe_allow_html=True)
        zone_status_placeholder = st.empty()

    with col_stats:
        stats_placeholder = st.empty()
        st.markdown("<br>", unsafe_allow_html=True)
        exit_placeholder = st.empty()
        st.markdown("<br>", unsafe_allow_html=True)
        alerts_placeholder = st.empty()

    # If not running, show static placeholder
    if not st.session_state.analysis_running:
        with video_placeholder.container():
            st.markdown("""
            <div class="glass-card">
                <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                    📹 Video Feed
                </h3>
                <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color);
                            border-radius: 12px; aspect-ratio: 16/9; display: flex;
                            align-items: center; justify-content: center; min-height: 400px;">
                    <div style="text-align: center; color: var(--text-tertiary);">
                        <div style="font-size: 3rem; margin-bottom: 1rem;"><i class="ph-duotone ph-video-camera"></i></div>
                        <p style="font-size: 1.125rem;">Press Start to begin analysis</p>
                        <p style="font-size: 0.9375rem;">Video loaded and ready</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Show last known data if available
        _render_static_panels(zone_status_placeholder, stats_placeholder,
                              exit_placeholder, alerts_placeholder)
        return

    # ═══ LIVE ANALYSIS LOOP ═══════════════════════════════════════════
    _run_analysis_loop(
        video_placeholder, zone_status_placeholder,
        stats_placeholder, exit_placeholder, alerts_placeholder,
        snapshot_clicked
    )


def _render_static_panels(zone_placeholder, stats_placeholder,
                           exit_placeholder, alerts_placeholder):
    """Render static/last-known panels when analysis is not running."""
    zone_names = {0: "Zone 1 (NW)", 1: "Zone 2 (NE)", 2: "Zone 3 (SW)", 3: "Zone 4 (SE)"}

    # Check if we have last-known data
    if 'last_zone_counts' in st.session_state:
        zone_counts = st.session_state.last_zone_counts
        zone_densities = st.session_state.get('last_zone_densities', {z: 0.0 for z in range(4)})
        zone_statuses = st.session_state.get('last_zone_statuses', {z: "SAFE" for z in range(4)})
    else:
        zone_counts = {z: 0 for z in range(4)}
        zone_densities = {z: 0.0 for z in range(4)}
        zone_statuses = {z: "SAFE" for z in range(4)}

    with zone_placeholder.container():
        st.markdown("""
        <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
            <i class="ph-duotone ph-scan"></i> Zone Status
        </h3>
        """, unsafe_allow_html=True)

        zcol1, zcol2 = st.columns(2)
        for z in range(4):
            col = zcol1 if z % 2 == 0 else zcol2
            with col:
                st.markdown(_build_zone_card_html(
                    z, zone_names[z], zone_statuses[z],
                    zone_counts[z], zone_densities[z], "→", "var(--text-tertiary)"
                ), unsafe_allow_html=True)
                if z < 2:
                    st.markdown("<br>", unsafe_allow_html=True)

    _render_stats_panel(stats_placeholder, zone_counts, zone_densities, zone_statuses)
    _render_exit_panel(exit_placeholder)
    _render_alerts_panel(alerts_placeholder, zone_statuses, zone_counts)


def _render_stats_panel(placeholder, zone_counts, zone_densities, zone_statuses):
    """Render the overall statistics panel."""
    total = sum(zone_counts.values())
    avg_density = sum(zone_densities.values()) / 4 if zone_densities else 0
    peak_zone = max(zone_densities, key=zone_densities.get, default=0)
    global_status = get_global_alert_level(zone_statuses)
    status_class = _get_status_class(global_status)

    with placeholder.container():
        st.markdown(
            '<div class="glass-card glow-cyan">'
            '<h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: \'Space Grotesk\', sans-serif;">'
            '<i class="ph-duotone ph-chart-bar"></i> Overall Stats</h3>'
            '<div style="text-align: center; margin-bottom: 1.5rem;">'
            '<p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.5rem;">Total People Detected</p>'
            f'<p style="color: var(--primary-cyan); font-size: 3rem; font-weight: 700;'
            f' font-family: \'Space Grotesk\', sans-serif; line-height: 1;">{total}</p></div>'
            '<div style="display: grid; grid-template-columns: 1fr; gap: 0.75rem;">'
            '<div style="background: var(--bg-tertiary); padding: 0.875rem; border-radius: 10px;'
            ' border: 1px solid var(--border-color);">'
            '<p style="color: var(--text-tertiary); font-size: 0.8125rem; margin-bottom: 0.25rem;">Avg Density</p>'
            f'<p style="color: var(--text-primary); font-size: 1.5rem; font-weight: 600;">{avg_density:.2f} p/m²</p></div>'
            '<div style="background: var(--bg-tertiary); padding: 0.875rem; border-radius: 10px;'
            ' border: 1px solid var(--border-color);">'
            '<p style="color: var(--text-tertiary); font-size: 0.8125rem; margin-bottom: 0.25rem;">Peak Zone</p>'
            f'<p style="color: var(--text-primary); font-size: 1.5rem; font-weight: 600;">Zone {peak_zone + 1}</p></div>'
            '<div style="background: var(--bg-tertiary); padding: 0.875rem; border-radius: 10px;'
            ' border: 1px solid var(--border-color);">'
            '<p style="color: var(--text-tertiary); font-size: 0.8125rem; margin-bottom: 0.25rem;">Status</p>'
            f'<span class="status-badge {status_class}">{global_status}</span></div>'
            '</div></div>',
            unsafe_allow_html=True
        )


def _render_exit_panel(placeholder):
    """Render the exit status panel."""
    exit_config = st.session_state.get('exit_config', DEFAULT_EXIT_CONFIG)
    zone_statuses = st.session_state.get('last_zone_statuses', {z: "SAFE" for z in range(4)})
    exit_statuses = get_exit_status(exit_config, zone_statuses)

    exit_cards_html = ""
    for idx, exit_info in enumerate(exit_config):
        status = exit_statuses.get(idx, "OPEN")
        icon = _get_exit_icon(status)
        border = _get_exit_border_color(status)
        zone_list = ", ".join([f"Zone {z+1}" for z in exit_info.get("zones", [])])
        name = exit_info.get('name', f'Exit {idx+1}')
        direction = exit_info.get('direction', '')

        exit_cards_html += (
            f'<div style="background: var(--bg-tertiary); padding: 0.875rem; border-radius: 10px;'
            f' border-left: 3px solid {border}; display: flex;'
            f' justify-content: space-between; align-items: center;">'
            f'<div><strong style="color: var(--text-primary);">{name} {direction}</strong>'
            f'<p style="color: var(--text-tertiary); font-size: 0.8125rem; margin: 0.25rem 0 0 0;">'
            f'{zone_list}</p></div>'
            f'<span style="font-size: 1.5rem;">{icon}</span></div>'
        )

    with placeholder.container():
        st.markdown(
            '<div class="glass-card">'
            '<h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: \'Space Grotesk\', sans-serif;">'
            '<i class="ph-duotone ph-door-open"></i> Exit Status</h3>'
            '<div style="display: grid; grid-template-columns: 1fr; gap: 0.75rem;">'
            f'{exit_cards_html}'
            '</div></div>',
            unsafe_allow_html=True
        )


def _render_alerts_panel(placeholder, zone_statuses, zone_counts):
    """Render the alerts and evacuation instructions panel."""
    global_status = get_global_alert_level(zone_statuses)
    summary = get_summary_message(zone_statuses, zone_counts)

    # Find zones with warnings or emergencies
    alert_zones = [z for z in range(4) if zone_statuses.get(z) in ("WARNING", "EMERGENCY")]

    alert_color = {
        "SAFE": "var(--status-success)",
        "MODERATE": "var(--status-moderate)",
        "WARNING": "var(--status-warning)",
        "EMERGENCY": "var(--status-danger)"
    }.get(global_status, "var(--text-tertiary)")

    alert_html = ""
    if alert_zones:
        for z in alert_zones:
            status = zone_statuses[z]
            color = "var(--status-danger)" if status == "EMERGENCY" else "var(--status-warning)"
            bg = "rgba(239, 68, 68, 0.1)" if status == "EMERGENCY" else "rgba(245, 158, 11, 0.1)"
            alert_html += (
                f'<div style="background: {bg}; padding: 1rem; border-radius: 8px;'
                f' border: 1px solid {color}; margin-bottom: 0.75rem;">'
                f'<strong style="color: {color};">Zone {z+1} {status}</strong>'
                f'<p style="color: var(--text-secondary); font-size: 0.875rem; margin: 0.5rem 0 0 0;">'
                f'{summary}</p></div>'
            )
    else:
        alert_html = (
            '<div style="background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 8px;'
            ' border: 1px solid var(--status-success);">'
            '<strong style="color: var(--status-success);">All Clear</strong>'
            '<p style="color: var(--text-secondary); font-size: 0.875rem; margin: 0.5rem 0 0 0;">'
            'All zones within safe density limits. Normal monitoring active.</p></div>'
        )

    with placeholder.container():
        st.markdown(
            f'<div class="glass-card" style="border-color: {alert_color};">'
            f'<h3 style="color: {alert_color}; margin-bottom: 1rem; font-family: \'Space Grotesk\', sans-serif;">'
            f'<i class="ph-duotone ph-warning"></i> Alerts</h3>'
            f'{alert_html}'
            f'</div>',
            unsafe_allow_html=True
        )


def _run_analysis_loop(video_placeholder, zone_status_placeholder,
                        stats_placeholder, exit_placeholder, alerts_placeholder,
                        snapshot_clicked):
    """Run the main video analysis loop."""

    # Load model
    model = load_yolo_model()

    # Get config from session state
    zone_config = st.session_state.get('zone_config', DEFAULT_ZONE_CONFIG)
    exit_config = st.session_state.get('exit_config', DEFAULT_EXIT_CONFIG)
    frame_skip = st.session_state.get('frame_skip', 2)
    confidence_threshold = st.session_state.get('confidence', 0.5)
    show_boxes = st.session_state.get('show_boxes', True)
    show_zones = st.session_state.get('show_zones', True)
    show_heatmap = st.session_state.get('show_heatmap', True)
    enable_audio = st.session_state.get('enable_audio', True)

    # Initialize timer manager
    if 'timer_manager' not in st.session_state:
        st.session_state.timer_manager = EmergencyTimerManager()
    timer_manager = st.session_state.timer_manager

    # Initialize audio system
    audio_system = get_audio_system(enabled=enable_audio)

    # Write video bytes to a temp file for OpenCV
    video_bytes = st.session_state.video_file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_file.write(video_bytes)
    temp_file.close()

    cap = cv2.VideoCapture(temp_file.name)

    if not cap.isOpened():
        video_placeholder.error("❌ Failed to open video file")
        os.unlink(temp_file.name)
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    zone_names = {0: "Zone 1 (NW)", 1: "Zone 2 (NE)", 2: "Zone 3 (SW)", 3: "Zone 4 (SE)"}
    frame_count = 0
    prev_counts = st.session_state.prev_zone_counts

    try:
        while cap.isOpened() and st.session_state.analysis_running:
            if st.session_state.analysis_paused:
                time.sleep(0.1)
                continue

            ret, frame = cap.read()
            if not ret:
                # Video ended - loop back or stop
                st.session_state.analysis_running = False
                break

            frame_count += 1

            # Skip frames for performance
            if frame_count % frame_skip != 0:
                continue

            # Process frame through the full pipeline
            processed_frame, detections, zone_counts, zone_densities, \
                zone_statuses, zone_timer_data = process_frame(
                    frame, model, zone_config, timer_manager
                )

            # Update audio alerts
            if enable_audio:
                audio_system.update_alert(zone_statuses)

            # Calculate exit statuses
            zone_exit_mapping = get_zone_exit_mapping(exit_config)
            exit_statuses = get_exit_status(exit_config, zone_statuses)

            # Store last known data
            st.session_state.last_zone_counts = zone_counts
            st.session_state.last_zone_densities = zone_densities
            st.session_state.last_zone_statuses = zone_statuses
            st.session_state.analysis_frame_count = frame_count

            # Accumulate session data for analytics
            st.session_state.session_data.append({
                'timestamp': datetime.now().isoformat(),
                'frame': frame_count,
                'total_people': sum(zone_counts.values()),
                'zone_counts': dict(zone_counts),
                'zone_densities': {str(k): round(v, 3) for k, v in zone_densities.items()},
                'zone_statuses': dict(zone_statuses),
                'global_status': get_global_alert_level(zone_statuses)
            })

            # Handle snapshot
            if snapshot_clicked:
                st.session_state.snapshot_frame = processed_frame.copy()
                snapshot_clicked = False

            # ─── Update UI ────────────────────────────────────────
            # Video feed
            frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

            # Zone status cards
            with zone_status_placeholder.container():
                st.markdown("""
                <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                    <i class="ph-duotone ph-scan"></i> Zone Status
                </h3>
                """, unsafe_allow_html=True)

                zcol1, zcol2 = st.columns(2)
                for z in range(4):
                    trend_arrow, trend_color = _get_trend_arrow(
                        zone_counts[z],
                        prev_counts[z] if prev_counts else None
                    )
                    col = zcol1 if z % 2 == 0 else zcol2
                    with col:
                        st.markdown(_build_zone_card_html(
                            z, zone_names[z], zone_statuses[z],
                            zone_counts[z], zone_densities[z],
                            trend_arrow, trend_color
                        ), unsafe_allow_html=True)
                        if z < 2:
                            st.markdown("<br>", unsafe_allow_html=True)

            # Stats panel
            _render_stats_panel(stats_placeholder, zone_counts, zone_densities, zone_statuses)

            # Exit panel
            st.session_state.last_exit_statuses = exit_statuses
            _render_exit_panel(exit_placeholder)

            # Alerts panel
            _render_alerts_panel(alerts_placeholder, zone_statuses, zone_counts)

            # Update previous counts for trend calculation
            prev_counts = dict(zone_counts)
            st.session_state.prev_zone_counts = prev_counts

            # Control frame rate
            time.sleep(1.0 / fps)

    finally:
        cap.release()
        os.unlink(temp_file.name)

        # Stop audio when done
        if enable_audio:
            audio_system.stop_alert()

        st.session_state.prev_zone_counts = prev_counts
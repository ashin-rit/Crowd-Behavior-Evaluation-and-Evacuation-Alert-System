"""
================================================================================
CONFIGURATION PAGE (REDESIGNED + BACKEND INTEGRATED)
================================================================================
Modern dark theme configuration interface with glassmorphism.
All settings are persisted to st.session_state for use by the analysis page.

Author: Ashin Saji
================================================================================
"""

import streamlit as st
import sys, os

# Add parent dir to path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    DEFAULT_ZONE_CONFIG, DEFAULT_EXIT_CONFIG, DEFAULT_NUM_EXITS,
    MIN_EXITS, MAX_EXITS, MIN_ZONE_AREA, MAX_ZONE_AREA, DEFAULT_ZONE_AREA,
    EXIT_DIRECTIONS, DENSITY_THRESHOLDS
)


def _init_config_defaults():
    """Initialize session state with default values if not already set."""
    if 'zone_config' not in st.session_state:
        st.session_state.zone_config = {
            k: dict(v) for k, v in DEFAULT_ZONE_CONFIG.items()
        }
    if 'exit_config' not in st.session_state:
        st.session_state.exit_config = [dict(e) for e in DEFAULT_EXIT_CONFIG]
    if 'frame_skip' not in st.session_state:
        st.session_state.frame_skip = 2
    if 'confidence' not in st.session_state:
        st.session_state.confidence = 0.5
    if 'show_boxes' not in st.session_state:
        st.session_state.show_boxes = True
    if 'show_zones' not in st.session_state:
        st.session_state.show_zones = True
    if 'show_heatmap' not in st.session_state:
        st.session_state.show_heatmap = True
    if 'enable_audio' not in st.session_state:
        st.session_state.enable_audio = True
    if 'enable_notifications' not in st.session_state:
        st.session_state.enable_notifications = False
    if 'log_events' not in st.session_state:
        st.session_state.log_events = True
    if 'config_saved' not in st.session_state:
        st.session_state.config_saved = False


def render():
    """Render the redesigned configuration page"""
    _init_config_defaults()

    # Page Header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 2.25rem; margin-bottom: 0.5rem; font-family: 'Space Grotesk', sans-serif;">
            <i class="ph-duotone ph-gear" style="color: var(--primary-cyan);"></i> <span class="gradient-text">System Configuration</span>
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.0625rem;">
            Configure detection zones, exits, and surveillance parameters
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ─── Video Upload Section ─────────────────────────────────────────
    st.markdown("### <i class='ph-duotone ph-video-camera'></i> Video Input", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                Upload CCTV Footage
            </h4>
            <p style="color: var(--text-secondary); font-size: 0.9375rem; margin-bottom: 1rem;">
                Supported formats: MP4, AVI, MOV • Max size: 200MB
            </p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'avi', 'mov'],
            help="Upload CCTV footage for crowd analysis",
            label_visibility="collapsed"
        )

        # Persist uploaded video to session state
        if uploaded_file is not None:
            st.session_state.video_file = uploaded_file.getvalue()
            st.session_state.video_name = uploaded_file.name

    with col2:
        has_video = 'video_file' in st.session_state and st.session_state.video_file is not None
        video_status = "File Loaded ✓" if has_video else "No Video"
        status_color = "var(--status-success)" if has_video else "var(--text-tertiary)"

        st.markdown(f"""
        <div class="glass-card" style="height: 100%;">
            <div style="text-align: center; padding: 1rem 0;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem; color: var(--secondary-blue);"><i class="ph-duotone ph-activity"></i></div>
                <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.25rem;">
                    Status
                </p>
                <p style="color: {status_color}; font-weight: 600; font-size: 1rem;">
                    {video_status}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Zone Configuration ───────────────────────────────────────────
    st.markdown("### <i class='ph-duotone ph-scan'></i> Detection Zones", unsafe_allow_html=True)

    use_default = st.checkbox("Use default zone configuration", value=True)

    if use_default:
        # Apply default zone areas
        for z in range(4):
            st.session_state.zone_config[z]['area'] = DEFAULT_ZONE_AREA

        zone_names = {0: "Zone 1 (NW)", 1: "Zone 2 (NE)", 2: "Zone 3 (SW)", 3: "Zone 4 (SE)"}
        zone_colors = {0: "var(--primary-cyan)", 1: "var(--secondary-blue)",
                       2: "var(--primary-cyan)", 3: "var(--secondary-blue)"}

        # Build zone cards HTML separately to avoid nested quote issues
        zone_cards = ""
        for z in range(4):
            zone_cards += (
                '<div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 10px;'
                ' border: 1px solid var(--border-color);">'
                f'<strong style="color: {zone_colors[z]};">{zone_names[z]}</strong>'
                f'<p style="color: var(--text-secondary); font-size: 0.875rem; margin: 0.5rem 0 0 0;">'
                f'Area: {DEFAULT_ZONE_AREA} m²</p></div>'
            )

        st.markdown(f"""
        <div class="glass-card">
            <p style="color: var(--text-secondary); font-size: 0.9375rem; margin-bottom: 1rem;">
                Using standard 2×2 grid with equal area distribution ({DEFAULT_ZONE_AREA}m² per zone)
            </p>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                {zone_cards}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="glass-card">
                <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                    North Zones
                </h4>
            </div>
            """, unsafe_allow_html=True)

            zone1_area = st.number_input("Zone 1 (NW) Area (m²)",
                min_value=MIN_ZONE_AREA, max_value=MAX_ZONE_AREA,
                value=st.session_state.zone_config[0]['area'], key="z1")
            zone2_area = st.number_input("Zone 2 (NE) Area (m²)",
                min_value=MIN_ZONE_AREA, max_value=MAX_ZONE_AREA,
                value=st.session_state.zone_config[1]['area'], key="z2")

        with col2:
            st.markdown("""
            <div class="glass-card">
                <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                    South Zones
                </h4>
            </div>
            """, unsafe_allow_html=True)

            zone3_area = st.number_input("Zone 3 (SW) Area (m²)",
                min_value=MIN_ZONE_AREA, max_value=MAX_ZONE_AREA,
                value=st.session_state.zone_config[2]['area'], key="z3")
            zone4_area = st.number_input("Zone 4 (SE) Area (m²)",
                min_value=MIN_ZONE_AREA, max_value=MAX_ZONE_AREA,
                value=st.session_state.zone_config[3]['area'], key="z4")

        # Store custom areas
        st.session_state.zone_config[0]['area'] = zone1_area
        st.session_state.zone_config[1]['area'] = zone2_area
        st.session_state.zone_config[2]['area'] = zone3_area
        st.session_state.zone_config[3]['area'] = zone4_area

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Exit Configuration ───────────────────────────────────────────
    st.markdown("### <i class='ph-duotone ph-door-open'></i> Exit Configuration", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        num_exits = st.slider(
            "Number of exits",
            min_value=MIN_EXITS,
            max_value=MAX_EXITS,
            value=max(MIN_EXITS, len(st.session_state.exit_config)),
            help="Total emergency exits in the venue"
        )

    with col2:
        st.markdown(f"""
        <div class="glass-card" style="display: flex; align-items: center; justify-content: center; height: 100%;">
            <div style="text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem; color: var(--status-success);"><i class="ph-duotone ph-door"></i></div>
                <p style="color: var(--text-primary); font-size: 1.5rem; font-weight: 600;
                          margin-bottom: 0.25rem; font-family: 'Space Grotesk', sans-serif;">
                    {num_exits} Exits
                </p>
                <p style="color: var(--text-secondary); font-size: 0.875rem;">
                    Currently configured
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Ensure exit_config list matches num_exits
    while len(st.session_state.exit_config) < num_exits:
        idx = len(st.session_state.exit_config)
        st.session_state.exit_config.append({
            "id": f"exit_{idx}",
            "name": f"Exit {idx + 1}",
            "direction": EXIT_DIRECTIONS[idx % len(EXIT_DIRECTIONS)],
            "capacity": 200,
            "zones": [idx % 4]
        })
    while len(st.session_state.exit_config) > num_exits:
        st.session_state.exit_config.pop()

    # Exit Details
    for i in range(num_exits):
        with st.expander(f"Exit {i+1} Configuration", expanded=(i < 2)):
            col1, col2 = st.columns(2)

            with col1:
                exit_name = st.text_input(
                    "Exit Name",
                    value=st.session_state.exit_config[i].get("name", f"Exit {i+1}"),
                    key=f"exit_name_{i}"
                )

                dir_options = EXIT_DIRECTIONS
                current_dir = st.session_state.exit_config[i].get("direction", "North")
                dir_index = dir_options.index(current_dir) if current_dir in dir_options else 0

                direction = st.selectbox(
                    "Direction",
                    options=dir_options,
                    index=dir_index,
                    key=f"exit_dir_{i}"
                )

            with col2:
                current_zones = st.session_state.exit_config[i].get("zones", [i % 4])
                zones = st.multiselect(
                    "Connected Zones",
                    options=[0, 1, 2, 3],
                    default=current_zones,
                    key=f"exit_zones_{i}",
                    help="Select zones (0-3) that can use this exit",
                    format_func=lambda x: f"Zone {x+1}"
                )

                capacity = st.number_input(
                    "Exit Capacity (people/min)",
                    min_value=10,
                    max_value=500,
                    value=st.session_state.exit_config[i].get("capacity", 200),
                    step=50,
                    key=f"exit_cap_{i}"
                )

            # Update exit config in session state
            st.session_state.exit_config[i] = {
                "id": f"exit_{i}",
                "name": exit_name,
                "direction": direction,
                "capacity": capacity,
                "zones": zones
            }

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Processing Parameters ────────────────────────────────────────
    st.markdown("### <i class='ph-duotone ph-sliders'></i> Processing Parameters", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                Performance
            </h4>
        </div>
        """, unsafe_allow_html=True)

        frame_skip = st.slider(
            "Frame skip",
            min_value=1,
            max_value=10,
            value=st.session_state.frame_skip,
            help="Process every Nth frame"
        )
        st.session_state.frame_skip = frame_skip

        confidence = st.slider(
            "Detection confidence",
            min_value=0.3,
            max_value=0.9,
            value=st.session_state.confidence,
            step=0.05,
            help="Minimum confidence threshold"
        )
        st.session_state.confidence = confidence

    with col2:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                Visualization
            </h4>
        </div>
        """, unsafe_allow_html=True)

        show_boxes = st.checkbox("Show bounding boxes", value=st.session_state.show_boxes)
        show_zones = st.checkbox("Show zone boundaries", value=st.session_state.show_zones)
        show_heatmap = st.checkbox("Show density heatmap", value=st.session_state.show_heatmap)

        st.session_state.show_boxes = show_boxes
        st.session_state.show_zones = show_zones
        st.session_state.show_heatmap = show_heatmap

    with col3:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                Alerts
            </h4>
        </div>
        """, unsafe_allow_html=True)

        enable_audio = st.checkbox("Audio alerts", value=st.session_state.enable_audio)
        enable_notifications = st.checkbox("Push notifications", value=st.session_state.enable_notifications)
        log_events = st.checkbox("Log all events", value=st.session_state.log_events)

        st.session_state.enable_audio = enable_audio
        st.session_state.enable_notifications = enable_notifications
        st.session_state.log_events = log_events

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ─── Action Buttons ───────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        col_left, col_right = st.columns(2)

        with col_left:
            if st.button("Save Configuration", use_container_width=True, type="primary"):
                # Validate
                has_video = 'video_file' in st.session_state and st.session_state.video_file is not None
                if not has_video:
                    st.warning("⚠️ No video uploaded yet. Config saved but you'll need a video for analysis.")

                st.session_state.config_saved = True
                st.success("✓ Configuration saved successfully!")
                st.balloons()

        with col_right:
            if st.button("Start Analysis", use_container_width=True):
                has_video = 'video_file' in st.session_state and st.session_state.video_file is not None
                if not has_video:
                    st.error("❌ Please upload a video file first")
                elif not st.session_state.config_saved:
                    st.warning("⚠️ Please save configuration first")
                else:
                    st.session_state.current_page = 'analysis'
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Configuration Summary ────────────────────────────────────────
    st.markdown("### <i class='ph-duotone ph-list-checks'></i> Configuration Summary", unsafe_allow_html=True)

    total_area = sum(st.session_state.zone_config[z]['area'] for z in range(4))

    st.markdown(f"""
    <div class="glass-card">
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem;">
            <div>
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.25rem;">
                    Detection Zones
                </p>
                <p style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;
                          font-family: 'Space Grotesk', sans-serif;">
                    4 Active
                </p>
            </div>
            <div>
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.25rem;">
                    Total Area
                </p>
                <p style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;
                          font-family: 'Space Grotesk', sans-serif;">
                    {total_area} m²
                </p>
            </div>
            <div>
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.25rem;">
                    Emergency Exits
                </p>
                <p style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;
                          font-family: 'Space Grotesk', sans-serif;">
                    {num_exits} Configured
                </p>
            </div>
            <div>
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.25rem;">
                    Processing Mode
                </p>
                <p style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;
                          font-family: 'Space Grotesk', sans-serif;">
                    {"Real-time" if frame_skip <= 3 else "Optimized"}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
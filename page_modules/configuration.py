"""
================================================================================
CONFIGURATION PAGE — HTML5 CANVAS ZONE & EXIT EDITOR
================================================================================
Interactive configuration with an embedded HTML5 Canvas (via
st.components.v1.html). JavaScript handles click-to-draw polygon zones
and exit-point placement; data flows back to Python through a hidden
Streamlit text_input that JS programmatically updates.

Author: Ashin Saji
================================================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import cv2
import sys
import os
import copy
import json
import base64
import tempfile
from PIL import Image

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Register the bi-directional canvas component (uses postMessage, not DOM hacks)
_CANVAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_canvas_component")
_canvas_editor = components.declare_component("canvas_editor", path=_CANVAS_DIR)

from config import (
    DEFAULT_POLYGON_ZONES, DEFAULT_EXIT_POINTS,
    MIN_EXITS, MAX_EXITS, MIN_ZONE_AREA, MAX_ZONE_AREA, DEFAULT_ZONE_AREA,
    MAX_ZONES, MIN_ZONES, DENSITY_THRESHOLDS
)


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================

def _init_config_defaults():
    """Initialize session state with default values if not already set."""
    if 'polygon_zones' not in st.session_state:
        st.session_state.polygon_zones = copy.deepcopy(DEFAULT_POLYGON_ZONES)
    if 'exit_points' not in st.session_state:
        st.session_state.exit_points = copy.deepcopy(DEFAULT_EXIT_POINTS)
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
    if 'zone_mode' not in st.session_state:
        st.session_state.zone_mode = "Use Default Zones"
    if 'exit_mode' not in st.session_state:
        st.session_state.exit_mode = "Use Default Exits"


# ==============================================================================
# VIDEO FRAME HELPERS
# ==============================================================================

def _get_first_frame_image():
    """Extract the first frame from the uploaded video as a PIL Image."""
    if 'video_file' not in st.session_state or st.session_state.video_file is None:
        return None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_file.write(st.session_state.video_file)
        temp_file.close()
        cap = cv2.VideoCapture(temp_file.name)
        ret, frame = cap.read()
        cap.release()
        os.unlink(temp_file.name)
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    except Exception:
        pass
    return None


def _frame_to_data_url(frame_rgb: np.ndarray, max_w: int = 800) -> str:
    """Encode a numpy RGB frame as a base64 data-URL for the canvas background."""
    h, w = frame_rgb.shape[:2]
    if w > max_w:
        scale = max_w / w
        new_w, new_h = max_w, int(h * scale)
        frame_rgb = cv2.resize(frame_rgb, (new_w, new_h))
    _, buf = cv2.imencode('.jpg', cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    b64 = base64.b64encode(buf).decode('utf-8')
    return f"data:image/jpeg;base64,{b64}"


def _draw_preview(frame_rgb: np.ndarray, zones: list, exits: list) -> np.ndarray:
    """Draw zone polygons and exit markers on a frame for static preview."""
    frame = frame_rgb.copy()
    h, w = frame.shape[:2]
    colors = [(0,255,255),(255,191,0),(0,255,0),(255,0,255),(255,255,0),(0,128,255),(128,0,255),(0,255,128)]

    for i, z in enumerate(zones):
        poly = z.get("polygon", [])
        if len(poly) < 3:
            continue
        pts = np.array([(int(p[0]*w), int(p[1]*h)) for p in poly], np.int32)
        c = colors[i % len(colors)]
        ov = frame.copy()
        cv2.fillPoly(ov, [pts], c)
        frame = cv2.addWeighted(ov, 0.15, frame, 0.85, 0)
        cv2.polylines(frame, [pts], True, c, 2)
        cx = int(sum(p[0]*w for p in poly) / len(poly))
        cy = int(sum(p[1]*h for p in poly) / len(poly))
        cv2.putText(frame, z.get("name", f"Zone {i+1}"), (cx-30, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2, cv2.LINE_AA)

    for ep in exits:
        ex, ey = int(ep["x_pct"]*w), int(ep["y_pct"]*h)
        c = (0,255,0) if ep.get("status","OPEN")=="OPEN" else (0,0,255)
        cv2.circle(frame, (ex,ey), 15, c, 3)
        cv2.circle(frame, (ex,ey), 6, c, -1)
        cv2.putText(frame, ep.get("name","Exit"), (ex-20,ey-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2, cv2.LINE_AA)
    return frame


# ==============================================================================
# HTML5 CANVAS WIDGET (self-contained JS)
# ==============================================================================

# Canvas widget is now in _canvas_component/index.html
# registered as _canvas_editor via declare_component above


# ==============================================================================
# RENDER FUNCTION
# ==============================================================================

def render():
    """Render the configuration page."""
    _init_config_defaults()

    is_running = st.session_state.get('analysis_running', False)

    # Page Header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 2.25rem; margin-bottom: 0.5rem; font-family: 'Space Grotesk', sans-serif;">
            <i class="ph-duotone ph-gear" style="color: var(--primary-cyan);"></i> <span class="gradient-text">System Configuration</span>
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.0625rem;">
            Configure detection zones, exit points, and surveillance parameters
        </p>
    </div>
    """, unsafe_allow_html=True)

    if is_running:
        st.warning("⚠️ Analysis is currently running. Zone and exit editing is disabled.")

    # ─── Video Upload ─────────────────────────────────────────────────
    st.markdown("### <i class='ph-duotone ph-video-camera'></i> Video Input", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                Upload CCTV Footage
            </h4>
            <p style="color: var(--text-secondary); font-size: 0.9375rem; margin-bottom: 1rem;">
                Supported formats: MP4, AVI, MOV
            </p>
        </div>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose a video file", type=['mp4','avi','mov'],
                                          help="Upload CCTV footage for crowd analysis",
                                          label_visibility="collapsed")
        if uploaded_file is not None:
            st.session_state.video_file = uploaded_file.getvalue()
            st.session_state.video_name = uploaded_file.name

    with col2:
        has_video = 'video_file' in st.session_state and st.session_state.video_file is not None
        vs = "File Loaded" if has_video else "No Video"
        vc = "var(--status-success)" if has_video else "var(--text-tertiary)"
        st.markdown(f"""
        <div class="glass-card" style="height: 100%;">
            <div style="text-align: center; padding: 1rem 0;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem; color: var(--secondary-blue);"><i class="ph-duotone ph-activity"></i></div>
                <p style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.25rem;">Status</p>
                <p style="color: {vc}; font-weight: 600; font-size: 1rem;">{vs}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Zone Configuration ───────────────────────────────────────────
    st.markdown("### <i class='ph-duotone ph-scan'></i> Detection Zones", unsafe_allow_html=True)

    if not is_running:
        _render_zone_editor()
    else:
        _render_zone_readonly()

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Exit Configuration ───────────────────────────────────────────
    st.markdown("### <i class='ph-duotone ph-door-open'></i> Exit Points", unsafe_allow_html=True)

    if not is_running:
        _render_exit_editor()
    else:
        _render_exit_readonly()

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Processing Parameters ────────────────────────────────────────
    st.markdown("### <i class='ph-duotone ph-sliders'></i> Processing Parameters", unsafe_allow_html=True)
    _render_processing_params()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ─── Action Buttons ──────────────────────────────────────────────
    _render_action_buttons()

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Summary ─────────────────────────────────────────────────────
    _render_config_summary()

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Preview ─────────────────────────────────────────────────────
    _render_preview()


# ==============================================================================
# ZONE EDITOR
# ==============================================================================

def _zones_match_defaults() -> bool:
    """Check if current polygon_zones match the default zone geometry."""
    current = st.session_state.polygon_zones
    defaults = DEFAULT_POLYGON_ZONES
    if len(current) != len(defaults):
        return False
    return all(
        c.get("polygon") == d.get("polygon")
        for c, d in zip(current, defaults)
    )


def _exits_match_defaults() -> bool:
    """Check if current exit_points match the default exit positions."""
    current = st.session_state.exit_points
    defaults = DEFAULT_EXIT_POINTS
    if len(current) != len(defaults):
        return False
    return all(
        c.get("x_pct") == d.get("x_pct") and c.get("y_pct") == d.get("y_pct")
        for c, d in zip(current, defaults)
    )

def _render_zone_editor():
    """Zone editor with mode selector: default grid or canvas drawing."""
    zone_mode = st.radio("Zone Setup Mode",
                          ["Use Default Zones", "Draw Custom Zones"],
                          horizontal=True, key="zone_mode",
                          help="Default uses 4 rectangular quadrants. Custom lets you draw polygons on the video frame.")

    if zone_mode == "Use Default Zones":
        st.session_state.polygon_zones = copy.deepcopy(DEFAULT_POLYGON_ZONES)
        _show_zone_cards(st.session_state.polygon_zones)
    else:
        # Clear defaults so only canvas-drawn zones are used
        if _zones_match_defaults():
            st.session_state.polygon_zones = []
        _render_zone_canvas()

    # Zone metadata editor (always shown)
    if st.session_state.polygon_zones:
        st.markdown("#### Zone Details")
        for i, zone in enumerate(st.session_state.polygon_zones):
            with st.expander(f"🔷 {zone['name']} ({len(zone['polygon'])} vertices)", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    new_name = st.text_input("Name", value=zone["name"], key=f"zname_{i}")
                with c2:
                    new_area = st.number_input("Area (m²)", min_value=MIN_ZONE_AREA,
                                                max_value=MAX_ZONE_AREA,
                                                value=zone["area"], key=f"zarea_{i}")
                st.session_state.polygon_zones[i]["name"] = new_name
                st.session_state.polygon_zones[i]["area"] = new_area
                verts = zone["polygon"]
                st.caption(f"Vertices: {', '.join(f'({v[0]:.1%}, {v[1]:.1%})' for v in verts)}")


def _render_zone_canvas():
    """Render the bi-directional canvas component for polygon zone drawing."""
    frame = _get_first_frame_image()
    if frame is None:
        st.info("📹 Upload a video first to draw custom zones on the first frame.")
        return

    st.markdown("""
    <div class="glass-card">
        <p style="color: var(--text-secondary); font-size: 0.9375rem;">
            <strong>Click</strong> on the frame to add polygon vertices.
            <strong>Double-click</strong> to close a polygon. Click <strong>Done — Apply</strong> when finished.
        </p>
    </div>
    """, unsafe_allow_html=True)

    h, w = frame.shape[:2]
    canvas_w = 720
    canvas_h = int(canvas_w * h / w)
    bg_url = _frame_to_data_url(frame, max_w=canvas_w)

    result = _canvas_editor(
        bg_url=bg_url, canvas_w=canvas_w, canvas_h=canvas_h,
        mode="zones",
        existing_zones=st.session_state.polygon_zones,
        existing_exits=st.session_state.exit_points,
        key="zone_canvas_editor", default=None,
        height=canvas_h + 80,
    )

    if result and isinstance(result, dict) and result.get("type") == "zones":
        raw = result.get("data", [])
        new_zones = []
        for idx, poly_coords in enumerate(raw):
            if len(poly_coords) >= 3:
                zone_id = f"zone_{idx}"
                # Try to find existing metadata by index first, then fallback
                existing = None
                if idx < len(st.session_state.polygon_zones):
                    existing = st.session_state.polygon_zones[idx]
                
                new_zones.append({
                    "id": zone_id,
                    "name": existing["name"] if existing else f"Zone {idx+1}",
                    "area": existing["area"] if existing else DEFAULT_ZONE_AREA,
                    "polygon": [tuple(p) for p in poly_coords],
                })
        
        # Only update and rerun if something actually changed
        if new_zones != st.session_state.polygon_zones:
            st.session_state.polygon_zones = new_zones
            st.rerun()


def _show_zone_cards(zones: list):
    """Display zone summary cards."""
    cards = ""
    for zone in zones:
        cards += (
            '<div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 10px;'
            ' border: 1px solid var(--border-color);">'
            f'<strong style="color: var(--primary-cyan);">{zone["name"]}</strong>'
            f'<p style="color: var(--text-secondary); font-size: 0.875rem; margin: 0.5rem 0 0 0;">'
            f'Area: {zone["area"]} m² • {len(zone["polygon"])} vertices</p></div>'
        )
    cols = min(len(zones), 4)
    st.markdown(f"""
    <div class="glass-card">
        <p style="color: var(--text-secondary); font-size: 0.9375rem; margin-bottom: 1rem;">
            Standard 2×2 grid with equal area distribution
        </p>
        <div style="display: grid; grid-template-columns: repeat({cols}, 1fr); gap: 1rem;">
            {cards}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_zone_readonly():
    """Show read-only zone config during analysis."""
    _show_zone_cards(st.session_state.polygon_zones)
    st.caption("🔒 Editing disabled during analysis")


# ==============================================================================
# EXIT EDITOR
# ==============================================================================

def _render_exit_editor():
    """Exit editor with mode selector: default or canvas placement."""
    exit_mode = st.radio("Exit Setup Mode",
                          ["Use Default Exits", "Place Custom Exits"],
                          horizontal=True, key="exit_mode",
                          help="Default places exits at edges. Custom lets you click-to-place on the frame.")

    if exit_mode == "Use Default Exits":
        st.session_state.exit_points = copy.deepcopy(DEFAULT_EXIT_POINTS)
    else:
        # Clear defaults so only canvas-placed exits are used
        if _exits_match_defaults():
            st.session_state.exit_points = []
        _render_exit_canvas()

    # Exit detail editors (always shown)
    _render_exit_list()


def _render_exit_canvas():
    """Render the bi-directional canvas component for exit point placement."""
    frame = _get_first_frame_image()
    if frame is None:
        st.info("📹 Upload a video first to place exit points on the frame.")
        return

    st.markdown("""
    <div class="glass-card">
        <p style="color: var(--text-secondary); font-size: 0.9375rem;">
            <strong>Click</strong> on the frame to place exit points. Click <strong>Done — Apply</strong> when finished.
        </p>
    </div>
    """, unsafe_allow_html=True)

    h, w = frame.shape[:2]
    canvas_w = 720
    canvas_h = int(canvas_w * h / w)
    bg_url = _frame_to_data_url(frame, max_w=canvas_w)

    result = _canvas_editor(
        bg_url=bg_url, canvas_w=canvas_w, canvas_h=canvas_h,
        mode="exits",
        existing_zones=st.session_state.polygon_zones,
        existing_exits=st.session_state.exit_points,
        key="exit_canvas_editor", default=None,
        height=canvas_h + 80,
    )

    if result and isinstance(result, dict) and result.get("type") == "exits":
        raw = result.get("data", [])
        new_exits = []
        for idx, pt in enumerate(raw):
            exit_id = f"exit_{idx}"
            existing = None
            if idx < len(st.session_state.exit_points):
                existing = st.session_state.exit_points[idx]

            new_exits.append({
                "id": exit_id,
                "name": existing["name"] if existing else f"Exit {idx+1}",
                "x_pct": pt["x_pct"],
                "y_pct": pt["y_pct"],
                "capacity": existing["capacity"] if existing else 20,
                "status": existing["status"] if existing else "OPEN",
            })
            
        if new_exits != st.session_state.exit_points:
            st.session_state.exit_points = new_exits
            st.rerun()


def _render_exit_list():
    """Render exit point detail editors."""
    if not st.session_state.exit_points:
        return

    st.markdown("#### Exit Details")
    for i, ep in enumerate(st.session_state.exit_points):
        with st.expander(f"🚪 {ep['name']} — ({ep['x_pct']:.1%}, {ep['y_pct']:.1%})", expanded=(i < 2)):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_name = st.text_input("Name", value=ep["name"], key=f"ename_{i}")
            with c2:
                new_cap = st.number_input("Capacity (ppl/min)", min_value=5, max_value=500,
                                           value=ep.get("capacity", 20), step=5, key=f"ecap_{i}")
            with c3:
                new_status = st.selectbox("Status", ["OPEN","BLOCKED"],
                                           index=0 if ep.get("status","OPEN")=="OPEN" else 1,
                                           key=f"estatus_{i}")
            st.session_state.exit_points[i]["name"] = new_name
            st.session_state.exit_points[i]["capacity"] = new_cap
            st.session_state.exit_points[i]["status"] = new_status


def _render_exit_readonly():
    """Show read-only exit config during analysis."""
    for ep in st.session_state.exit_points:
        sc = "var(--status-success)" if ep["status"] == "OPEN" else "var(--status-danger,#F00)"
        st.markdown(f"""
        <div class="glass-card" style="margin-bottom: 0.5rem;">
            <span style="color: {sc}; font-weight: 600;">●</span>
            <strong style="color: var(--text-primary);">{ep['name']}</strong>
            <span style="color: var(--text-secondary); font-size: 0.875rem;">
                — Capacity: {ep.get('capacity',20)}/min • {ep['status']}
            </span>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# PROCESSING PARAMETERS
# ==============================================================================

def _render_processing_params():
    """Render processing parameter controls."""
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">Performance</h4>
        </div>
        """, unsafe_allow_html=True)
        frame_skip = st.slider("Frame skip", 1, 10, st.session_state.frame_skip, help="Process every Nth frame")
        st.session_state.frame_skip = frame_skip
        confidence = st.slider("Detection confidence", 0.3, 0.9, st.session_state.confidence, 0.05)
        st.session_state.confidence = confidence

    with c2:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">Visualization</h4>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.show_boxes = st.checkbox("Bounding boxes", st.session_state.show_boxes)
        st.session_state.show_zones = st.checkbox("Zone overlays", st.session_state.show_zones)
        st.session_state.show_heatmap = st.checkbox("Density heatmap", st.session_state.show_heatmap)

    with c3:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">Alerts</h4>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.enable_audio = st.checkbox("Audio alerts", st.session_state.enable_audio)
        st.session_state.enable_notifications = st.checkbox("Push notifications", st.session_state.enable_notifications)
        st.session_state.log_events = st.checkbox("Log events", st.session_state.log_events)


# ==============================================================================
# ACTION BUTTONS
# ==============================================================================

def _render_action_buttons():
    """Render save and start buttons."""
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        cl, cr = st.columns(2)
        with cl:
            if st.button("Save Configuration", width='stretch', type="primary"):
                if not st.session_state.polygon_zones:
                    st.error("❌ At least one detection zone is required.")
                    return
                st.session_state.config_saved = True
                st.success("✓ Configuration saved!")
                st.balloons()
        with cr:
            if st.button("Start Analysis", width='stretch'):
                has_video = 'video_file' in st.session_state and st.session_state.video_file is not None
                if not has_video:
                    st.error("❌ Upload a video first")
                elif not st.session_state.config_saved:
                    st.warning("⚠️ Save configuration first")
                else:
                    st.session_state.current_page = 'analysis'
                    st.rerun()


# ==============================================================================
# CONFIG SUMMARY
# ==============================================================================

def _render_config_summary():
    """Render configuration summary panel."""
    st.markdown("### <i class='ph-duotone ph-list-checks'></i> Configuration Summary", unsafe_allow_html=True)
    nz = len(st.session_state.polygon_zones)
    ta = sum(z.get("area", 0) for z in st.session_state.polygon_zones)
    ne = len(st.session_state.exit_points)
    oe = sum(1 for e in st.session_state.exit_points if e.get("status") == "OPEN")
    fs = st.session_state.frame_skip

    st.markdown(f"""
    <div class="glass-card">
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem;">
            <div>
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.25rem;">Zones</p>
                <p style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;
                          font-family: 'Space Grotesk', sans-serif;">{nz} Active</p>
            </div>
            <div>
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.25rem;">Total Area</p>
                <p style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;
                          font-family: 'Space Grotesk', sans-serif;">{ta} m²</p>
            </div>
            <div>
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.25rem;">Exits</p>
                <p style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;
                          font-family: 'Space Grotesk', sans-serif;">{oe}/{ne} Open</p>
            </div>
            <div>
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.25rem;">Mode</p>
                <p style="color: var(--text-primary); font-size: 1.25rem; font-weight: 600;
                          font-family: 'Space Grotesk', sans-serif;">{"Real-time" if fs <= 3 else "Optimized"}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# PREVIEW
# ==============================================================================

def _render_preview():
    """Render zone + exit overlay preview on the first frame."""
    frame = _get_first_frame_image()
    if frame is None:
        return
    st.markdown("### <i class='ph-duotone ph-eye'></i> Live Preview", unsafe_allow_html=True)
    preview = _draw_preview(frame, st.session_state.polygon_zones, st.session_state.exit_points)
    st.image(preview, caption="Zone & Exit Preview (First Frame)", width='stretch')
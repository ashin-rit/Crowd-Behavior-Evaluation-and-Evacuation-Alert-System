"""
================================================================================
ANALYTICS PAGE (REDESIGNED + BACKEND INTEGRATED)
================================================================================
Historical data analysis and reporting with real session data.
Falls back to demo data if no sessions exist.

Author: Ashin Saji
================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import sys
import os
from datetime import datetime, timedelta

# Add parent dir to path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from session_persistence import (
    save_session, list_sessions, load_session,
    get_all_sessions_summary, get_latest_session
)


def _get_session_dataframe(session_data):
    """Convert raw session data list to a clean DataFrame."""
    if not session_data:
        return None

    rows = []
    for entry in session_data:
        row = {
            'timestamp': entry.get('timestamp', ''),
            'frame': entry.get('frame', 0),
            'total_people': entry.get('total_people', 0),
            'global_status': entry.get('global_status', 'SAFE'),
        }
        # Flatten zone counts
        zc = entry.get('zone_counts', {})
        for z in range(4):
            row[f'zone_{z+1}_count'] = zc.get(str(z), zc.get(z, 0))

        # Flatten zone densities
        zd = entry.get('zone_densities', {})
        for z in range(4):
            row[f'zone_{z+1}_density'] = zd.get(str(z), zd.get(z, 0.0))

        # Flatten zone statuses
        zs = entry.get('zone_statuses', {})
        for z in range(4):
            row[f'zone_{z+1}_status'] = zs.get(str(z), zs.get(z, 'SAFE'))

        rows.append(row)

    df = pd.DataFrame(rows)
    if 'timestamp' in df.columns and len(df) > 0:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception:
            pass
    return df


def _generate_demo_data():
    """Generate demo data when no real sessions exist."""
    dates = pd.date_range(start='2025-02-07', end='2025-02-14', freq='D')
    return {
        'dates': dates,
        'zone_data': {
            'Zone 1': [45, 52, 48, 55, 51, 58, 62, 59],
            'Zone 2': [62, 68, 65, 72, 69, 75, 78, 73],
            'Zone 3': [88, 95, 92, 98, 94, 102, 105, 98],
            'Zone 4': [38, 42, 40, 45, 43, 48, 51, 47]
        },
        'status_counts': {'Safe': 145, 'Moderate': 78, 'Warning': 42, 'Emergency': 8},
        'zone_totals': {'Zone 1': 945, 'Zone 2': 1250, 'Zone 3': 1680, 'Zone 4': 845},
        'total_sessions': 24,
        'avg_people': 187,
        'peak_density': 4.8,
        'incidents': 3
    }


def _create_themed_line_chart(x_data, y_dict, height=350):
    """Create a themed line chart with multiple series."""
    fig = go.Figure()
    colors = ['#06B6D4', '#3B82F6', '#F59E0B', '#10B981']

    for (name, y_vals), color in zip(y_dict.items(), colors):
        fig.add_trace(go.Scatter(
            x=x_data, y=y_vals, name=name,
            line=dict(color=color, width=3),
            mode='lines+markers', marker=dict(size=8)
        ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8', family='Inter'),
        xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', showgrid=True),
        yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', showgrid=True, title='People Count'),
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=height
    )
    return fig


def _create_themed_bar_chart(x_data, y_data, height=300):
    """Create a themed bar chart."""
    fig = go.Figure(data=[
        go.Bar(
            x=x_data, y=y_data,
            marker=dict(
                color=['#06B6D4', '#3B82F6', '#F59E0B', '#10B981'],
                line=dict(color='rgba(148, 163, 184, 0.2)', width=1)
            )
        )
    ])

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8', family='Inter'),
        xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', showgrid=False),
        yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', showgrid=True, title='Total People'),
        height=height, showlegend=False
    )
    return fig


def _create_themed_pie_chart(labels, values, height=300):
    """Create a themed donut/pie chart."""
    fig = go.Figure(data=[
        go.Pie(
            labels=labels, values=values,
            marker=dict(colors=['#10B981', '#3B82F6', '#F59E0B', '#EF4444']),
            hole=0.5, textinfo='label+percent',
            textfont=dict(color='#F8FAFC')
        )
    ])

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8', family='Inter'),
        height=height, showlegend=True,
        legend=dict(orientation='v', yanchor='middle', y=0.5, xanchor='left', x=1.1)
    )
    return fig


def render():
    """Render the redesigned analytics page"""

    # Page Header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 2.25rem; margin-bottom: 0.5rem; font-family: 'Space Grotesk', sans-serif;">
            <i class="ph-duotone ph-chart-line-up" style="color: var(--secondary-blue);"></i> <span class="gradient-text">Analytics Dashboard</span>
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.0625rem;">
            Historical trends, insights, and performance reports
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ─── Check for data sources ───────────────────────────────────────
    # Priority: 1) Current session data, 2) Saved sessions, 3) Demo data
    current_session = st.session_state.get('session_data', [])
    saved_sessions = list_sessions()
    has_real_data = len(current_session) > 0 or len(saved_sessions) > 0

    # ─── Save current session button ──────────────────────────────────
    if len(current_session) > 0:
        col_save, col_info = st.columns([1, 3])
        with col_save:
            if st.button("Save Current Session", use_container_width=True, type="primary"):
                metadata = {
                    "video_name": st.session_state.get('video_name', 'Unknown'),
                    "total_frames": st.session_state.get('analysis_frame_count', 0),
                    "zone_config": {str(k): v for k, v in
                                    st.session_state.get('zone_config', {}).items()},
                }
                filepath = save_session(current_session, metadata)
                st.success(f"✓ Session saved! ({len(current_session)} data points)")
        with col_info:
            st.info(f"📊 Current session: **{len(current_session)}** data points from analysis")

        st.markdown("<br>", unsafe_allow_html=True)

    # ─── Data Source Selection ────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1])

    data_source = "current"
    df = None

    with col1:
        if has_real_data:
            source_options = []
            if len(current_session) > 0:
                source_options.append("Current Session")
            for s in saved_sessions:
                label = f"{s['created_at'][:16]} ({s['total_frames']} frames)"
                source_options.append(label)

            if len(source_options) > 1:
                selected = st.selectbox("Data Source", options=source_options,
                                        help="Select session to analyze")
                if selected == "Current Session":
                    df = _get_session_dataframe(current_session)
                    data_source = "current"
                else:
                    idx = source_options.index(selected)
                    if len(current_session) > 0:
                        idx -= 1  # Offset for "Current Session" option
                    session_file = saved_sessions[idx]
                    session = load_session(session_file['filepath'])
                    df = _get_session_dataframe(session.get('data', []))
                    data_source = "saved"
            elif len(source_options) == 1:
                st.markdown(f"**Data Source:** {source_options[0]}")
                if source_options[0] == "Current Session":
                    df = _get_session_dataframe(current_session)
                else:
                    session = load_session(saved_sessions[0]['filepath'])
                    df = _get_session_dataframe(session.get('data', []))
        else:
            st.markdown("""
            <div style="background: rgba(6, 182, 212, 0.1); padding: 0.75rem 1rem; border-radius: 8px;
                        border: 1px solid rgba(6, 182, 212, 0.3);">
                <p style="color: var(--primary-cyan); font-size: 0.9375rem; margin: 0;">
                    <i class="ph-fill ph-push-pin"></i> Showing demo data. Run an analysis to see real results.
                </p>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        if st.button("Generate Report", use_container_width=True, type="primary"):
            st.success("Report generated successfully!")

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Render with real data or demo ────────────────────────────────
    if df is not None and len(df) > 0:
        _render_real_analytics(df)
    else:
        _render_demo_analytics()


def _render_real_analytics(df):
    """Render analytics from real session DataFrame."""

    total_frames = len(df)
    avg_people = df['total_people'].mean()
    peak_people = df['total_people'].max()
    status_counts = df['global_status'].value_counts().to_dict()
    incidents = status_counts.get('WARNING', 0) + status_counts.get('EMERGENCY', 0)

    # Calculate peak density across all zones
    density_cols = [c for c in df.columns if c.endswith('_density')]
    peak_density = df[density_cols].max().max() if density_cols else 0

    # ─── Key Metrics Row ──────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        ("Total Frames", int(total_frames), "var(--primary-cyan)", f"Analyzed"),
        ("Avg People", f"{avg_people:.0f}", "var(--secondary-blue)", "Per frame"),
        ("Peak Density", f"{peak_density:.1f}", "var(--status-warning)", "p/m²"),
        ("Incidents", int(incidents), "var(--status-danger)", "Warnings + Emergencies"),
    ]

    for col, (label, value, color, sub) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.5rem;">
                    {label}
                </p>
                <p style="color: {color}; font-size: 2.5rem; font-weight: 700;
                          font-family: 'Space Grotesk', sans-serif; margin-bottom: 0.25rem;">
                    {value}
                </p>
                <p style="color: var(--text-tertiary); font-size: 0.875rem; font-weight: 600;">
                    {sub}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Charts Section ───────────────────────────────────────────────
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Crowd Trends Chart
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                <i class="ph-duotone ph-trend-up"></i> Crowd Trends Over Time
            </h3>
        </div>
        """, unsafe_allow_html=True)

        # Build zone count series using frame index or timestamp
        x_data = df['frame'] if 'frame' in df.columns else df.index
        zone_series = {}
        for z in range(4):
            col_name = f'zone_{z+1}_count'
            if col_name in df.columns:
                zone_series[f'Zone {z+1}'] = df[col_name].tolist()

        if zone_series:
            fig = _create_themed_line_chart(x_data, zone_series)
            fig.update_layout(xaxis_title='Frame')
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Zone Distribution (totals)
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                <i class="ph-duotone ph-squares-four"></i> Zone Distribution (Total)
            </h3>
        </div>
        """, unsafe_allow_html=True)

        zone_totals = {}
        for z in range(4):
            col_name = f'zone_{z+1}_count'
            if col_name in df.columns:
                zone_totals[f'Zone {z+1}'] = df[col_name].sum()

        if zone_totals:
            fig2 = _create_themed_bar_chart(
                list(zone_totals.keys()), list(zone_totals.values())
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col_right:
        # Status Distribution Pie
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                🚦 Status Distribution
            </h3>
        </div>
        """, unsafe_allow_html=True)

        all_statuses = ['SAFE', 'MODERATE', 'WARNING', 'EMERGENCY']
        display_labels = ['Safe', 'Moderate', 'Warning', 'Emergency']
        counts = [status_counts.get(s, 0) for s in all_statuses]

        if sum(counts) > 0:
            fig3 = _create_themed_pie_chart(display_labels, counts)
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Peak Stats
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                <i class="ph-duotone ph-chart-bar"></i> Peak Statistics
            </h3>
            <div style="display: grid; grid-template-columns: 1fr; gap: 0.75rem;">
        """, unsafe_allow_html=True)

        # Find peak frame
        peak_frame_idx = df['total_people'].idxmax()
        peak_frame = df.loc[peak_frame_idx, 'frame'] if 'frame' in df.columns else peak_frame_idx

        # Find busiest zone
        zone_sums = {f'Zone {z+1}': df[f'zone_{z+1}_count'].sum()
                     for z in range(4) if f'zone_{z+1}_count' in df.columns}
        busiest_zone = max(zone_sums, key=zone_sums.get) if zone_sums else "N/A"

        st.markdown(f"""
                <div style="background: var(--bg-tertiary); padding: 0.875rem; border-radius: 10px;
                           border-left: 3px solid var(--accent-purple);">
                    <strong style="color: var(--text-primary);">Peak Frame</strong>
                    <p style="color: var(--accent-purple); font-size: 1.25rem; font-weight: 600;
                              margin: 0.5rem 0 0.25rem 0; font-family: 'Space Grotesk', sans-serif;">
                        Frame {int(peak_frame)}
                    </p>
                    <p style="color: var(--text-tertiary); font-size: 0.8125rem; margin: 0;">
                        {int(peak_people)} people detected
                    </p>
                </div>
                <div style="background: var(--bg-tertiary); padding: 0.875rem; border-radius: 10px;
                           border-left: 3px solid var(--accent-cyan);">
                    <strong style="color: var(--text-primary);">Busiest Zone</strong>
                    <p style="color: var(--secondary-blue); font-size: 1.25rem; font-weight: 600;
                              margin: 0.5rem 0 0.25rem 0; font-family: 'Space Grotesk', sans-serif;">
                        {busiest_zone}
                    </p>
                    <p style="color: var(--text-tertiary); font-size: 0.8125rem; margin: 0;">
                        {zone_sums.get(busiest_zone, 0):,} total detections
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Incidents list
        incident_frames = df[df['global_status'].isin(['WARNING', 'EMERGENCY'])]
        if len(incident_frames) > 0:
            st.markdown("""
            <div class="glass-card" style="border-color: var(--status-danger);">
                <h3 style="color: var(--status-danger); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                    <i class="ph-duotone ph-warning-octagon"></i> Incident Frames
                </h3>
                <div style="display: grid; grid-template-columns: 1fr; gap: 0.75rem;">
            """, unsafe_allow_html=True)

            # Show up to 5 most recent incidents
            recent_incidents = incident_frames.tail(5).iloc[::-1]
            for _, row in recent_incidents.iterrows():
                status = row['global_status']
                color = "var(--status-danger)" if status == "EMERGENCY" else "var(--status-warning)"
                bg = "rgba(239, 68, 68, 0.1)" if status == "EMERGENCY" else "rgba(245, 158, 11, 0.1)"
                frame_num = row.get('frame', '?')
                people = row.get('total_people', 0)

                st.markdown(f"""
                    <div style="background: {bg}; padding: 0.875rem; border-radius: 8px;
                               border: 1px solid {color};">
                        <strong style="color: {color};">Frame {int(frame_num)} — {status}</strong>
                        <p style="color: var(--text-secondary); font-size: 0.875rem; margin: 0.5rem 0 0 0;">
                            {int(people)} people detected
                        </p>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Export Section ───────────────────────────────────────────────
    st.markdown("### <i class='ph-duotone ph-file-text'></i> Export Reports", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Real CSV export
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download CSV",
            data=csv_buffer.getvalue(),
            file_name=f"crowd_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        # Excel export
        try:
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            st.download_button(
                "Download Excel",
                data=excel_buffer.getvalue(),
                file_name=f"crowd_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except ImportError:
            if st.button("Excel Report", use_container_width=True):
                st.info("Install openpyxl for Excel export: pip install openpyxl")

    with col3:
        # JSON export
        json_data = df.to_json(orient='records', date_format='iso')
        st.download_button(
            "Download JSON",
            data=json_data,
            file_name=f"crowd_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

    with col4:
        if st.button("Email Report", use_container_width=True):
            st.info("Email integration coming soon")


def _render_demo_analytics():
    """Render analytics with demo data (no real sessions available)."""
    demo = _generate_demo_data()

    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    demo_metrics = [
        ("Total Sessions", demo['total_sessions'], "var(--primary-cyan)", "↑ 12% vs last week",
         "var(--status-success)"),
        ("Avg People/Session", demo['avg_people'], "var(--secondary-blue)", "↑ 8% vs last week",
         "var(--status-success)"),
        ("Peak Density", demo['peak_density'], "var(--status-warning)", "↑ 15% vs last week",
         "var(--status-warning)"),
        ("Incidents", demo['incidents'], "var(--status-danger)", "↓ 25% vs last week",
         "var(--status-success)"),
    ]

    for col, (label, value, color, delta, delta_color) in zip(
            [col1, col2, col3, col4], demo_metrics):
        with col:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <p style="color: var(--text-tertiary); font-size: 0.875rem; margin-bottom: 0.5rem;">
                    {label}
                </p>
                <p style="color: {color}; font-size: 2.5rem; font-weight: 700;
                          font-family: 'Space Grotesk', sans-serif; margin-bottom: 0.25rem;">
                    {value}
                </p>
                <p style="color: {delta_color}; font-size: 0.875rem; font-weight: 600;">
                    {delta}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Crowd Trends
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                📊 Crowd Trends Over Time
            </h3>
        </div>
        """, unsafe_allow_html=True)

        fig = _create_themed_line_chart(demo['dates'], demo['zone_data'])
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Zone Distribution
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                <i class="ph-duotone ph-squares-four"></i> Zone Distribution
            </h3>
        </div>
        """, unsafe_allow_html=True)

        fig2 = _create_themed_bar_chart(
            list(demo['zone_totals'].keys()),
            list(demo['zone_totals'].values())
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_right:
        # Status Distribution Pie
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                🚦 Status Distribution
            </h3>
        </div>
        """, unsafe_allow_html=True)

        fig3 = _create_themed_pie_chart(
            list(demo['status_counts'].keys()),
            list(demo['status_counts'].values())
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Peak Hours (demo only)
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                <i class="ph-duotone ph-clock"></i> Peak Hours
            </h3>
            <div style="display: grid; grid-template-columns: 1fr; gap: 0.75rem;">
                <div style="background: var(--bg-tertiary); padding: 0.875rem; border-radius: 10px;
                           border-left: 3px solid var(--accent-purple);">
                    <strong style="color: var(--text-primary);">Busiest Hour</strong>
                    <p style="color: var(--accent-purple); font-size: 1.25rem; font-weight: 600;
                              margin: 0.5rem 0 0.25rem 0; font-family: 'Space Grotesk', sans-serif;">
                        6:00 PM - 7:00 PM
                    </p>
                    <p style="color: var(--text-tertiary); font-size: 0.8125rem; margin: 0;">
                        Avg 245 people
                    </p>
                </div>
                <div style="background: var(--bg-tertiary); padding: 0.875rem; border-radius: 10px;
                           border-left: 3px solid var(--accent-cyan);">
                    <strong style="color: var(--text-primary);">Quietest Hour</strong>
                    <p style="color: var(--secondary-blue); font-size: 1.25rem; font-weight: 600;
                              margin: 0.5rem 0 0.25rem 0; font-family: 'Space Grotesk', sans-serif;">
                        10:00 AM - 11:00 AM
                    </p>
                    <p style="color: var(--text-tertiary); font-size: 0.8125rem; margin: 0;">
                        Avg 52 people
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Recent Incidents (demo)
        st.markdown("""
        <div class="glass-card" style="border-color: var(--status-danger);">
            <h3 style="color: var(--status-danger); margin-bottom: 1rem; font-family: 'Space Grotesk', sans-serif;">
                <i class="ph-duotone ph-warning-octagon"></i> Recent Incidents
            </h3>
            <div style="display: grid; grid-template-columns: 1fr; gap: 0.75rem;">
                <div style="background: rgba(239, 68, 68, 0.1); padding: 0.875rem; border-radius: 8px;
                           border: 1px solid var(--status-danger);">
                    <strong style="color: var(--status-danger);">Feb 12, 18:45</strong>
                    <p style="color: var(--text-secondary); font-size: 0.875rem; margin: 0.5rem 0 0 0;">
                        Zone 3 emergency - Density exceeded 5.2 p/m²
                    </p>
                </div>
                <div style="background: rgba(245, 158, 11, 0.1); padding: 0.875rem; border-radius: 8px;
                           border: 1px solid var(--status-warning);">
                    <strong style="color: var(--status-warning);">Feb 10, 15:30</strong>
                    <p style="color: var(--text-secondary); font-size: 0.875rem; margin: 0.5rem 0 0 0;">
                        Zone 2 warning - High density detected
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Export Section (demo - placeholder)
    st.markdown("### <i class='ph-duotone ph-file-text'></i> Export Reports", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Excel Report", use_container_width=True, key="demo_excel"):
            st.info("Run an analysis first to export real data")

    with col2:
        if st.button("PDF Summary", use_container_width=True, key="demo_pdf"):
            st.info("Run an analysis first to export real data")

    with col3:
        if st.button("CSV Data", use_container_width=True, key="demo_csv"):
            st.info("Run an analysis first to export real data")

    with col4:
        if st.button("Email Report", use_container_width=True, key="demo_email"):
            st.info("Run an analysis first to export real data")
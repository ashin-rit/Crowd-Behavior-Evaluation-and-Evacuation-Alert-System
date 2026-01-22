"""
================================================================================
CROWD EVALUATION SYSTEM - MULTI-PAGE APPLICATION (REDESIGNED)
================================================================================
Modern dark theme with purple/cyan accents matching mobile UI aesthetics

Pages:
    1. Home - System overview and dashboard
    2. Configuration - System setup and parameters
    3. Live Analysis - Real-time video processing
    4. Analytics - Reports and insights

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="CrowdEval • AI Surveillance",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS matching mobile UI elements
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Import Phosphor Icons */
    @import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css');
    @import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/fill/style.css');
    @import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/duotone/style.css');
    
    /* Global Theme */
    .glass-card, .status-badge {
        box-sizing: border-box;
    }
    
    :root {
        /* 
           Cyan-Blue Design System 
           Primary Palette: Cyan (#06B6D4) & Blue (#3B82F6)
        */
        /* Main Accent Colors */
        --primary-cyan: #06B6D4;
        --primary-cyan-dark: #0891B2;
        --primary-cyan-light: #22D3EE;
        --primary-cyan-lighter: #67E8F9;
        
        /* Supporting Blues */
        --secondary-blue: #3B82F6;
        --secondary-blue-dark: #2563EB;
        --secondary-blue-light: #60A5FA;
        
        /* Backgrounds */
        --bg-primary: #0f1117;
        --bg-secondary: #1a1d2e;
        --bg-tertiary: #252836;
        --bg-card: #1e2139;
        
        /* Text */
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
        --text-tertiary: #64748B;
        
        /* Status */
        --status-safe: #10B981;     /* Green */
        --status-success: #10B981;  /* Green */
        --status-moderate: #06B6D4; /* Cyan (Info/Moderate) */
        --status-info: #06B6D4;     /* Cyan */
        --status-warning: #F59E0B;  /* Amber */
        --status-danger: #EF4444;   /* Red */
        --status-emergency: #EF4444; /* Red */
        
        /* UI Elements */
        --border-color: rgba(148, 163, 184, 0.1);
        --border-hover: rgba(6, 182, 212, 0.3);
        --shadow-cyan: 0 0 20px rgba(6, 182, 212, 0.3);
        --shadow-cyan-strong: 0 0 30px rgba(6, 182, 212, 0.5);
    }
    
    /* Main App Background */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }
    
    .main {
        background: var(--bg-primary);
        padding: 1.5rem;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--text-primary) !important;
        font-weight: 700 !important;
    }
    
    h1 {
        font-size: 2.5rem !important;
        background: linear-gradient(135deg, var(--primary-cyan), var(--secondary-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        border-right: 1px solid rgba(6, 182, 212, 0.1);
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* Hide Sidebar Toggle (Restored Visibility as per previous fixes, ensuring it's visible but styled if needed) */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    
    /* Sidebar Header */
    [data-testid="stSidebar"] h1 {
        font-size: 1.75rem !important;
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }
    
    /* Navigation Buttons */
    .stButton > button {
        width: 100%;
        background: var(--bg-tertiary);
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 0.875rem 1rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.9375rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-sm);
        text-align: left;
        margin-bottom: 0.5rem;
    }
    
    .stButton > button:hover {
        background: var(--bg-card);
        border-color: var(--primary-cyan);
        color: var(--text-primary);
        transform: translateX(4px);
        box-shadow: var(--shadow-md);
    }
    
    /* Primary Button (Active Page / Action) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-cyan) 0%, var(--primary-cyan-dark) 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4);
        transition: all 0.3s ease;
        font-weight: 600;
        border-radius: 10px;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--primary-cyan-light) 0%, var(--primary-cyan) 100%) !important;
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.6);
        transform: translateY(-2px);
    }
    
    /* Secondary Button (Inactive Page) */
    .stButton > button[kind="secondary"] {
        background: var(--bg-tertiary) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--primary-cyan) !important;
        color: var(--primary-cyan) !important;
        background: rgba(6, 182, 212, 0.1) !important;
    }
    
    /* Text & Paragraphs */
    p, span, div, label {
        color: var(--text-secondary) !important;
        font-size: 0.9375rem;
        line-height: 1.6;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.8125rem !important;
    }
    
    /* Cards & Containers */
    .element-container {
        background: transparent;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-size: 0.9375rem !important;
        padding: 0.625rem 0.875rem !important;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border-color: var(--primary-cyan) !important;
        box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1) !important;
        outline: none;
    }
    
    /* Sliders */
    .stSlider > div > div > div > div {
        background: var(--primary-cyan) !important;
    }
    
    .stSlider > div > div > div {
        background: var(--bg-tertiary) !important;
    }
    
    /* Checkboxes */
    .stCheckbox > label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        color: var(--text-primary) !important;
        font-weight: 600;
        padding: 0.75rem 1rem;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--primary-cyan);
        background: var(--bg-card);
    }
    
    .streamlit-expanderContent {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-top: none;
        border-radius: 0 0 10px 10px;
        padding: 1rem;
    }
    
    /* Info/Alert Boxes */
    .stAlert {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        color: var(--text-secondary) !important;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: var(--border-color);
        margin: 1.5rem 0;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: var(--bg-tertiary);
        border: 2px dashed var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary-cyan);
        background: var(--bg-card);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--bg-tertiary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-cyan);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--primary-cyan) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* ===================================
       MULTISELECT (ZONE TAGS) - CYAN THEME
       =================================== */
    
    /* Zone tag pills - Cyan gradient */
    .stMultiSelect [data-baseweb="tag"] {
        background: linear-gradient(135deg, var(--primary-cyan), var(--primary-cyan-dark)) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.375rem 0.75rem !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        box-shadow: 0 2px 4px rgba(6, 182, 212, 0.2) !important;
        transition: all 0.3s ease !important;
        margin: 0.25rem !important;
    }
    
    .stMultiSelect [data-baseweb="tag"]:hover {
        background: linear-gradient(135deg, var(--primary-cyan-light), var(--primary-cyan)) !important;
        box-shadow: 0 4px 8px rgba(6, 182, 212, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Remove button (×) on tags */
    .stMultiSelect [data-baseweb="tag"] svg {
        fill: white !important;
        opacity: 0.8 !important;
        transition: opacity 0.2s !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] svg:hover {
        opacity: 1 !important;
    }
    
    /* Multiselect container */
    .stMultiSelect > div > div {
        background: #e8e9eb !important;
        border-radius: 10px !important;
        border: 2px solid #3d4354 !important;
        padding: 0.5rem !important;
        min-height: 52px !important;
        transition: all 0.3s ease !important;
    }
    
    .stMultiSelect > div > div:focus-within {
        border-color: var(--primary-cyan) !important;
        box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1) !important;
    }
    
    /* Dropdown icon */
    .stMultiSelect svg[viewBox="0 0 20 20"] {
        fill: var(--primary-cyan) !important;
    }
    
    /* Dropdown menu */
    .stMultiSelect [role="listbox"] {
        background: var(--bg-card) !important;
        border: 1px solid rgba(6, 182, 212, 0.2) !important;
        border-radius: 10px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
    }
    
    .stMultiSelect [role="option"] {
        color: var(--text-secondary) !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.2s !important;
    }
    
    .stMultiSelect [role="option"]:hover {
        background: rgba(6, 182, 212, 0.1) !important;
        color: var(--text-primary) !important;
    }
    
    .stMultiSelect [role="option"][aria-selected="true"] {
        background: rgba(6, 182, 212, 0.2) !important;
        color: var(--primary-cyan) !important;
    }
    
    /* Multiselect input field */
    .stMultiSelect input {
        color: #1e2230 !important;
        font-weight: 500 !important;
    }
    
    .stMultiSelect input::placeholder {
        color: #6b7280 !important;
    }
    
    /* ===================================
       SELECTBOX ENHANCEMENTS
       =================================== */
    
    .stSelectbox > div > div {
        background: var(--bg-tertiary) !important;
        border: 2px solid #3d4354 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: var(--primary-cyan) !important;
    }
    
    .stSelectbox svg {
        fill: var(--primary-cyan) !important;
    }
    
    .stSelectbox [data-baseweb="popover"] {
        background: var(--bg-card) !important;
        border: 1px solid rgba(6, 182, 212, 0.2) !important;
        border-radius: 10px !important;
    }
    
    .stSelectbox [role="option"]:hover {
        background: rgba(6, 182, 212, 0.1) !important;
    }
    
    /* ===================================
       NUMBER INPUT STYLING
       =================================== */
    
    .stNumberInput > div > div {
        background: #e8e9eb !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    
    .stNumberInput > div > div > input {
        background: transparent !important;
        border: none !important;
        color: #1e2230 !important;
        text-align: center !important;
        font-weight: 600 !important;
        font-size: 0.9375rem !important;
    }
    
    .stNumberInput > div > div > input:focus {
        box-shadow: none !important;
        background: transparent !important;
    }
    
    /* Plus/Minus buttons */
    .stNumberInput button {
        background: transparent !important;
        border: none !important;
        color: #6b7280 !important;
        font-size: 1.125rem !important;
        padding: 0.875rem 1rem !important;
        transition: all 0.2s !important;
    }
    
    .stNumberInput button:hover {
        color: #1e2230 !important;
        background: rgba(0, 0, 0, 0.05) !important;
    }
    
    .stNumberInput button:active {
        background: rgba(0, 0, 0, 0.1) !important;
    }
    
    .stNumberInput button svg {
        fill: currentColor !important;
    }
    
    /* ===================================
       EXPANDER HEADER STYLING
       =================================== */
    
    .streamlit-expanderHeader {
        background: #e8e9eb !important;
        color: #6b7280 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: #f3f4f6 !important;
        color: #1e2230 !important;
    }
    
    .streamlit-expanderHeader svg {
        fill: #6b7280 !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover svg {
        fill: var(--primary-cyan) !important;
    }
    
    .streamlit-expanderContent {
        background: #1e2230 !important;
        border: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 1.5rem 1.25rem !important;
    }
    
    /* ===================================
       CUSTOM GLASS CARD COMPONENT
       =================================== */
    
    .glass-card {
        background: rgba(30, 33, 57, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(6, 182, 212, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px rgba(6, 182, 212, 0.2);
        border-color: rgba(6, 182, 212, 0.3);
    }
    
    /* ===================================
       STATUS BADGES
       =================================== */
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.375rem 0.875rem;
        border-radius: 20px;
        font-size: 0.8125rem;
        font-weight: 600;
        letter-spacing: 0.025em;
    }
    
    .status-safe {
        background: rgba(16, 185, 129, 0.1);
        color: var(--status-success);
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    .status-moderate {
        background: rgba(6, 182, 212, 0.1);
        color: var(--status-moderate);
        border: 1px solid rgba(6, 182, 212, 0.2);
    }
    
    .status-warning {
        background: rgba(245, 158, 11, 0.1);
        color: var(--status-warning);
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    
    .status-emergency {
        background: rgba(239, 68, 68, 0.1);
        color: var(--status-danger);
        border: 1px solid rgba(239, 68, 68, 0.2);
        animation: pulse-danger 2s infinite;
    }
    
    @keyframes pulse-danger {
        0%, 100% {
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
        }
        50% {
            box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
        }
    }
    
    /* ===================================
       GRADIENT TEXT UTILITY
       =================================== */
    
    .gradient-text {
        background: linear-gradient(135deg, var(--primary-cyan), var(--secondary-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Main welcome page
def main():
    # Sidebar navigation
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0 0.5rem 0;">
        <div style="width: 48px; height: 48px; margin: 0 auto 0.75rem auto; 
                    background: linear-gradient(135deg, var(--primary-cyan), var(--primary-cyan-dark));
                    border-radius: 12px; display: flex; align-items: center; justify-content: center;
                    box-shadow: var(--shadow-cyan); font-size: 1.5rem; color: white;">
            <i class="ph-duotone ph-scan"></i>
        </div>
        <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; 
                   margin-bottom: 0.25rem;">CrowdEval</h1>
        <p style="color: var(--text-tertiary); font-size: 0.8125rem; font-family: 'Inter', sans-serif;">
            AI Surveillance System v2.0
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### Navigation")
    
    # Navigation pages
    pages = {
        "Home": "home",
        "Configuration": "config", 
        "Live Analysis": "analysis",
        "Analytics": "analytics"
    }
    
    # Initialize session state for navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    # Display navigation buttons
    for page_name, page_key in pages.items():
        is_current = st.session_state.current_page == page_key
        button_type = "primary" if is_current else "secondary"
        
        if st.sidebar.button(page_name, key=f"nav_{page_key}", 
                            use_container_width=True, type=button_type):
            st.session_state.current_page = page_key
            st.rerun()
    
    st.sidebar.markdown("---")
    
    # System status sidebar
    st.sidebar.markdown("### System Status")
    st.sidebar.markdown("""
    <div class="glass-card" style="margin-top: 0.75rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <span style="color: var(--text-secondary); font-size: 0.875rem;">
                <i class="ph ph-brain" style="color: var(--primary-cyan); margin-right: 4px;"></i> Neural Net
            </span>
            <span class="status-badge status-safe">ONLINE</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <span style="color: var(--text-secondary); font-size: 0.875rem;">
                <i class="ph ph-camera" style="color: var(--secondary-blue); margin-right: 4px;"></i> Detector
            </span>
            <span class="status-badge status-safe">READY</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <span style="color: var(--text-secondary); font-size: 0.875rem;">
                <i class="ph ph-squares-four" style="color: var(--text-tertiary); margin-right: 4px;"></i> Active Zones
            </span>
            <span style="color: var(--primary-cyan); font-weight: 600; font-size: 0.9375rem;">4</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: var(--text-secondary); font-size: 0.875rem;">
                <i class="ph ph-cpu" style="color: var(--text-tertiary); margin-right: 4px;"></i> AI Model
            </span>
            <span style="color: var(--secondary-blue); font-weight: 600; font-size: 0.9375rem;">YOLOv8</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <p style="color: var(--text-tertiary); font-size: 0.8125rem;">
            MCA Final Year Project<br>
            <span style="color: var(--primary-cyan); font-weight: 600;">Ashin Saji</span> © 2025
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Route to appropriate page
    if st.session_state.current_page == 'home':
        show_home()
    elif st.session_state.current_page == 'config':
        show_config()
    elif st.session_state.current_page == 'analysis':
        show_analysis()
    elif st.session_state.current_page == 'analytics':
        show_analytics()


def show_home():
    """Home/Dashboard page"""
    from page_modules import home
    home.render()


def show_config():
    """Configuration page"""
    from page_modules import configuration
    configuration.render()


def show_analysis():
    """Live Analysis page"""
    from page_modules import analysis
    analysis.render()


def show_analytics():
    """Analytics/Reports page"""
    from page_modules import analytics
    analytics.render()


if __name__ == "__main__":
    main()
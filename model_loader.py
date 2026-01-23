"""
Model loading logic for YOLOv8.
"""
import streamlit as st
from ultralytics import YOLO

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

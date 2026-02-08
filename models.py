"""
================================================================================
YOLO MODEL LOADING MODULE
================================================================================
Handles loading and caching of the YOLOv8 model for person detection.

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

import streamlit as st
from ultralytics import YOLO


@st.cache_resource
def load_yolo_model(model_path: str = 'yolov8n.pt') -> YOLO:
    """
    Load the YOLOv8 model with Streamlit caching.
    
    Uses @st.cache_resource decorator to cache the model in memory,
    preventing expensive reloading on every frame or session refresh.
    
    Args:
        model_path: Path to the YOLO model weights file.
                   Defaults to 'yolov8n.pt' (nano model for speed).
    
    Returns:
        YOLO: Loaded YOLOv8 model ready for inference.
    
    Notes:
        - YOLOv8 nano is used for balance between speed and accuracy
        - Model weights are auto-downloaded on first run if not present
        - Class 0 in COCO dataset is 'person'
    """
    model = YOLO(model_path)
    return model

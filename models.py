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
from config import YOLO_MODEL_PATH


@st.cache_resource
def load_yolo_model(model_path: str = YOLO_MODEL_PATH) -> YOLO:
    """
    Load the YOLOv8 model with Streamlit caching.
    
    Uses @st.cache_resource decorator to cache the model in memory,
    preventing expensive reloading on every frame or session refresh.
    
    Args:
        model_path: Path to the YOLO model weights file.
                   Defaults to the custom trained model in config.YOLO_MODEL_PATH.
    
    Returns:
        YOLO: Loaded YOLOv8 model ready for inference.
    
    Notes:
        - Uses custom trained weights optimized for crowd detection
        - Model weights should be located in the models/ directory
        - Class 0 in typical YOLO is 'person'
    """
    model = YOLO(model_path)
    return model

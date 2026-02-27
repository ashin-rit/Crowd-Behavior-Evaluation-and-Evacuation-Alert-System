import streamlit as st
from ultralytics import YOLO
from config import YOLO_MODEL_PATH


@st.cache_resource
def load_yolo_model(model_path: str = YOLO_MODEL_PATH) -> YOLO:

    model = YOLO(model_path)
    return model

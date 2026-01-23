"""
Main processing pipeline for video frames.
Computes detections, updates zone status, and draws visualizations.
"""
import cv2
import numpy as np
from ultralytics import YOLO

from config import STATUS_COLORS_BGR
from logic import get_zone, get_status
from visualization import draw_zone_overlay, draw_zone_grid, draw_zone_hud

def process_frame(frame: np.ndarray, model: YOLO, threshold: int) -> tuple:
    """
    Main processing function for each video frame.
    
    Args:
        frame: Input video frame (BGR format)
        model: Loaded YOLO model
        threshold: Capacity threshold for zone classification
        
    Returns:
        tuple: (processed_frame, zone_counts, zone_statuses)
            - processed_frame: Frame with all visualizations
            - zone_counts: Dict mapping zone index to people count
            - zone_statuses: Dict mapping zone index to status string
    """
    frame_height, frame_width = frame.shape[:2]
    
    # Initialize zone counts
    zone_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    
    # Run YOLO inference
    # classes=[0] filters for 'person' class only
    results = model(frame, classes=[0], verbose=False)
    
    # Process detections
    detections = []
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Get bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            
            # Calculate center point of bounding box
            # This is used to determine which zone the person is in
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            
            # Determine zone based on center point
            zone = get_zone(cx, cy, frame_width, frame_height)
            zone_counts[zone] += 1
            
            detections.append({
                'bbox': (x1, y1, x2, y2),
                'center': (cx, cy),
                'zone': zone,
                'confidence': confidence
            })
    
    # Calculate status for each zone
    zone_statuses = {}
    for zone in range(4):
        zone_statuses[zone] = get_status(zone_counts[zone], threshold)
    
    # Draw visualizations
    # Step 1: Draw heatmap overlays for each zone
    for zone in range(4):
        frame = draw_zone_overlay(frame, zone, zone_statuses[zone], 
                                  frame_width, frame_height)
    
    # Step 2: Draw bounding boxes on detected people
    # Color is based on the zone's current status
    for detection in detections:
        x1, y1, x2, y2 = detection['bbox']
        zone = detection['zone']
        status = zone_statuses[zone]
        color = STATUS_COLORS_BGR[status]
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw confidence label
        label = f"{detection['confidence']:.2f}"
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, color, 2, cv2.LINE_AA)
    
    # Step 3: Draw grid lines
    frame = draw_zone_grid(frame, frame_width, frame_height)
    
    # Step 4: Draw HUD for each zone
    for zone in range(4):
        frame = draw_zone_hud(frame, zone, zone_counts[zone], 
                             zone_statuses[zone], frame_width, frame_height)
    
    return frame, zone_counts, zone_statuses

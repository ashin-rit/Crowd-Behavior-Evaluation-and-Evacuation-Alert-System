# Intelligent Crowd Behavior Evaluation & Evacuation System

An MCA Final Year Project for analyzing CCTV footage to detect crowd density, classify risk levels using a "Traffic Light" system, and generate real-time evacuation instructions.

## Features

- **YOLO-based Person Detection**: Uses YOLOv8 nano model for efficient person detection
- **Smart Grid Zone Division**: Automatically divides video into 2x2 grid (4 zones)
- **Traffic Light Classification**: 
  - 🟢 Safe (0-50% threshold)
  - 🟡 Warning (50-85% threshold)  
  - 🔴 Emergency (>85% threshold)
- **Heatmap Overlays**: Visual density representation with color-coded zones
- **Real-time Evacuation Alerts**: Automatic instructions with designated exits
- **Audio Alarm Simulation**: Flashing banner for emergency situations

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

## Zone Layout

```
+-------------------+-------------------+
|      Zone 1       |      Zone 2       |
|    (Top-Left)     |    (Top-Right)    |
|   Exit: North     |    Exit: East     |
+-------------------+-------------------+
|      Zone 3       |      Zone 4       |
|   (Bottom-Left)   |   (Bottom-Right)  |
|   Exit: West      |    Exit: South    |
+-------------------+-------------------+
```

## Author

Ashin Saji - MCA Final Year Project

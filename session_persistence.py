"""
================================================================================
SESSION PERSISTENCE MODULE
================================================================================
Saves and loads analysis session data to/from JSON files for historical
analytics across multiple sessions.

Author: Ashin Saji
================================================================================
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


# Directory where session files are stored
SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")


def _ensure_sessions_dir():
    """Create the sessions directory if it doesn't exist."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)


def save_session(session_data: List[Dict], metadata: Optional[Dict] = None) -> str:
    """
    Save a completed analysis session to a JSON file.
    
    Args:
        session_data: List of per-frame data dicts from the analysis loop
        metadata: Optional dict with session metadata (video name, config, etc.)
    
    Returns:
        str: Path to the saved session file
    """
    _ensure_sessions_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{timestamp}.json"
    filepath = os.path.join(SESSIONS_DIR, filename)

    session = {
        "id": timestamp,
        "created_at": datetime.now().isoformat(),
        "metadata": metadata or {},
        "total_frames": len(session_data),
        "data": session_data
    }

    with open(filepath, 'w') as f:
        json.dump(session, f, indent=2, default=str)

    return filepath


def load_session(filepath: str) -> Dict:
    """Load a session from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def list_sessions() -> List[Dict]:
    """
    List all saved sessions with summary info.
    
    Returns:
        List of dicts with: filename, created_at, total_frames, filepath
    """
    _ensure_sessions_dir()
    sessions = []

    for filename in sorted(os.listdir(SESSIONS_DIR), reverse=True):
        if filename.endswith('.json'):
            filepath = os.path.join(SESSIONS_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                sessions.append({
                    "filename": filename,
                    "filepath": filepath,
                    "created_at": data.get("created_at", "Unknown"),
                    "total_frames": data.get("total_frames", 0),
                    "metadata": data.get("metadata", {})
                })
            except (json.JSONDecodeError, KeyError):
                continue

    return sessions


def get_latest_session() -> Optional[Dict]:
    """Get the most recent saved session data."""
    sessions = list_sessions()
    if sessions:
        return load_session(sessions[0]["filepath"])
    return None


def get_all_sessions_summary() -> List[Dict]:
    """
    Get summary statistics for all sessions.
    
    Returns:
        List of dicts with: session_id, created_at, total_frames,
        avg_people, peak_people, incidents_count
    """
    _ensure_sessions_dir()
    summaries = []

    for filename in sorted(os.listdir(SESSIONS_DIR), reverse=True):
        if filename.endswith('.json'):
            filepath = os.path.join(SESSIONS_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    session = json.load(f)

                data = session.get("data", [])
                if not data:
                    continue

                people_counts = [d.get("total_people", 0) for d in data]
                statuses = [d.get("global_status", "SAFE") for d in data]

                summaries.append({
                    "session_id": session.get("id", filename),
                    "created_at": session.get("created_at", "Unknown"),
                    "total_frames": len(data),
                    "avg_people": sum(people_counts) / len(people_counts) if people_counts else 0,
                    "peak_people": max(people_counts) if people_counts else 0,
                    "incidents_count": sum(1 for s in statuses if s in ("WARNING", "EMERGENCY")),
                    "video_name": session.get("metadata", {}).get("video_name", "Unknown"),
                    "filepath": filepath
                })
            except (json.JSONDecodeError, KeyError):
                continue

    return summaries

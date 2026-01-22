"""
================================================================================
AUDIO ALERT SYSTEM
================================================================================
Generates beep patterns based on crowd density threat levels

Author: Ashin Saji
MCA Final Year Project
================================================================================
"""

import time
import threading
from typing import Dict, Optional
import platform

# Try importing audio libraries (with fallbacks)
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

try:
    import numpy as np
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False


class AudioAlertSystem:
    """
    Manages audio alerts with different beep patterns for threat levels.
    
    Beep Patterns:
    - SAFE: No sound
    - MODERATE: Single beep every 5 seconds
    - WARNING: Double beep every 3 seconds
    - EMERGENCY: Triple beep every 1 second
    - CRITICAL: Continuous rapid beeps
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize audio alert system.
        
        Args:
            enabled: Whether audio alerts are enabled
        """
        self.enabled = enabled
        self.current_alert = "SAFE"
        self.alert_thread = None
        self.stop_flag = False
        
        # Beep parameters
        self.frequency = 1500  # Hz (tone frequency)
        self.duration_short = 0.25  # seconds (short beep)
        self.duration_long = 0.3  # seconds (long beep)
        
        # Alert patterns: (beeps_count, interval_between_alerts)
        self.patterns = {
            "SAFE": (0, 0),           # No beep
            "MODERATE": (1, 5.0),     # 1 beep every 5 seconds
            "WARNING": (2, 3.0),      # 2 beeps every 3 seconds
            "EMERGENCY": (3, 1.0),    # 3 beeps every 1 second
            "CRITICAL": (5, 0.5)      # 5 beeps every 0.5 seconds (continuous)
        }
    
    def _generate_beep_tone(self, duration: float = 0.2) -> np.ndarray:
        """
        Generate a beep tone using numpy.
        
        Args:
            duration: Beep duration in seconds
            
        Returns:
            numpy array of audio samples
        """
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Generate sine wave
        wave = np.sin(2 * np.pi * self.frequency * t)
        wave = wave / np.max(np.abs(wave))
        
        # Apply envelope (fade in/out) to avoid clicks
        envelope = np.ones_like(wave)
        fade_samples = int(0.01 * sample_rate)  # 10ms fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        return wave * envelope * 0.8 # 30% volume
    
    def _play_beep_sounddevice(self, duration: float = 0.2):
        """Play beep using sounddevice library."""
        if not HAS_SOUNDDEVICE:
            return
        
        try:
            tone = self._generate_beep_tone(duration)
            sd.play(tone, samplerate=44100)
            sd.wait()
        except Exception as e:
            print(f"Sounddevice error: {e}")
    
    def _play_beep_winsound(self, duration: float = 0.2):
        """Play beep using Windows winsound."""
        if not HAS_WINSOUND:
            return
        
        try:
            duration_ms = int(duration * 1000)
            winsound.Beep(self.frequency, duration_ms)
        except Exception as e:
            print(f"Winsound error: {e}")
    
    def _play_beep_system(self):
        """Play beep using system bell (fallback)."""
        import os
        system = platform.system()
        
        try:
            if system == "Windows":
                # Console beep
                print("\a", end="", flush=True)
            elif system == "Darwin":  # macOS
                os.system("osascript -e 'beep 1'")
            else:  # Linux
                os.system("beep -f 1000 -l 200 2>/dev/null || echo -ne '\\007'")
        except Exception as e:
            print(f"System beep error: {e}")
    
    def play_beep(self, duration: float = 0.2):
        """
        Play a single beep using the best available method.
        
        Priority:
        1. sounddevice (best quality, cross-platform)
        2. winsound (Windows only, good quality)
        3. system beep (fallback, basic)
        
        Args:
            duration: Beep duration in seconds
        """
        if not self.enabled:
            return
        
        # Try methods in order of preference
        if HAS_SOUNDDEVICE:
            self._play_beep_sounddevice(duration)
        elif HAS_WINSOUND:
            self._play_beep_winsound(duration)
        else:
            self._play_beep_system()
    
    def _alert_loop(self):
        """Background thread that continuously plays alert pattern."""
        while not self.stop_flag:
            if self.current_alert == "SAFE":
                time.sleep(0.1)
                continue
            
            beeps_count, interval = self.patterns.get(self.current_alert, (0, 0))
            
            if beeps_count == 0:
                time.sleep(0.1)
                continue
            
            # Play pattern
            for i in range(beeps_count):
                if self.stop_flag:
                    break
                
                # Play beep
                self.play_beep(self.duration_short)
                
                # Short pause between beeps in pattern
                if i < beeps_count - 1:
                    time.sleep(0.15)
            
            # Wait for interval before next pattern
            if not self.stop_flag:
                time.sleep(interval)
    
    def start_alert(self, alert_level: str):
        """
        Start playing alert pattern for given level.
        
        Args:
            alert_level: One of SAFE, MODERATE, WARNING, EMERGENCY, CRITICAL
        """
        if not self.enabled:
            return
        
        # Stop current alert if running
        self.stop_alert()
        
        # Validate alert level
        if alert_level not in self.patterns:
            print(f"Invalid alert level: {alert_level}")
            return
        
        self.current_alert = alert_level
        
        # Start background thread for continuous alerts
        if alert_level != "SAFE":
            self.stop_flag = False
            self.alert_thread = threading.Thread(target=self._alert_loop, daemon=True)
            self.alert_thread.start()
    
    def stop_alert(self):
        """Stop the current alert."""
        self.stop_flag = True
        if self.alert_thread and self.alert_thread.is_alive():
            self.alert_thread.join(timeout=1.0)
        self.current_alert = "SAFE"
    
    def update_alert(self, zone_statuses: Dict[int, str]):
        """
        Update alert based on zone statuses.
        
        Priority:
        1. If 2+ zones are EMERGENCY → CRITICAL
        2. If any zone is EMERGENCY → EMERGENCY
        3. If any zone is WARNING → WARNING
        4. If any zone is MODERATE → MODERATE
        5. Otherwise → SAFE
        
        Args:
            zone_statuses: Dict mapping zone index to status string
        """
        if not self.enabled:
            return
        
        statuses = list(zone_statuses.values())
        
        # Count emergencies
        emergency_count = statuses.count("EMERGENCY")
        
        # Determine alert level
        if emergency_count >= 2:
            new_alert = "CRITICAL"
        elif "EMERGENCY" in statuses:
            new_alert = "EMERGENCY"
        elif "WARNING" in statuses:
            new_alert = "WARNING"
        elif "MODERATE" in statuses:
            new_alert = "MODERATE"
        else:
            new_alert = "SAFE"
        
        # Only restart if alert level changed
        if new_alert != self.current_alert:
            self.start_alert(new_alert)
    
    def test_all_patterns(self):
        """Test all beep patterns (for demonstration)."""
        print("Testing Audio Alert System...")
        print("=" * 50)
        
        for level in ["MODERATE", "WARNING", "EMERGENCY", "CRITICAL"]:
            beeps, interval = self.patterns[level]
            print(f"\n{level}: {beeps} beep(s) every {interval}s")
            print("Playing pattern for 5 seconds...")
            
            self.start_alert(level)
            time.sleep(5)
            self.stop_alert()
            
            time.sleep(1)  # Pause between tests
        
        print("\n" + "=" * 50)
        print("Test complete!")
    
    def enable(self):
        """Enable audio alerts."""
        self.enabled = True
    
    def disable(self):
        """Disable audio alerts."""
        self.stop_alert()
        self.enabled = False
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop_alert()


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

# Global instance (singleton pattern)
_audio_system = None

def get_audio_system(enabled: bool = True) -> AudioAlertSystem:
    """
    Get or create the global audio alert system.
    
    Args:
        enabled: Whether audio is enabled
        
    Returns:
        AudioAlertSystem instance
    """
    global _audio_system
    if _audio_system is None:
        _audio_system = AudioAlertSystem(enabled=enabled)
    return _audio_system


def play_single_beep():
    """Play a single test beep."""
    system = get_audio_system()
    system.play_beep()


def start_alert(alert_level: str):
    """
    Start alert pattern.
    
    Args:
        alert_level: SAFE, MODERATE, WARNING, EMERGENCY, or CRITICAL
    """
    system = get_audio_system()
    system.start_alert(alert_level)


def stop_alert():
    """Stop current alert."""
    system = get_audio_system()
    system.stop_alert()


def update_from_zones(zone_statuses: Dict[int, str]):
    """
    Update alert based on zone statuses.
    
    Args:
        zone_statuses: Dict mapping zone to status
    """
    system = get_audio_system()
    system.update_alert(zone_statuses)


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == "__main__":
    # Test the audio system
    audio = AudioAlertSystem(enabled=True)
    
    print("Audio Alert System Test")
    print("=" * 50)
    print("\nAvailable libraries:")
    print(f"  - sounddevice: {HAS_SOUNDDEVICE}")
    print(f"  - winsound: {HAS_WINSOUND}")
    
    input("\nPress Enter to test all patterns...")
    audio.test_all_patterns()
    
    print("\n✅ Test complete!")
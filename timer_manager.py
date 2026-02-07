"""
Emergency Timer Manager
Tracks elapsed time for each zone in emergency state
"""

import time
from datetime import datetime, timedelta

class EmergencyTimerManager:
    """Manages emergency timers for all zones"""
    
    def __init__(self):
        self.zone_timers = {}  # {zone_id: {'start_time': timestamp, 'elapsed': seconds}}
        self.flash_state = {}  # {zone_id: True/False} for flashing effect
        self.last_flash_toggle = {}  # {zone_id: timestamp}
    
    def start_timer(self, zone_id):
        """Start timer for a zone entering emergency"""
        if zone_id not in self.zone_timers:
            self.zone_timers[zone_id] = {
                'start_time': time.time(),
                'elapsed': 0
            }
            self.flash_state[zone_id] = True
            self.last_flash_toggle[zone_id] = time.time()
    
    def update_timer(self, zone_id):
        """Update elapsed time for active timer"""
        if zone_id in self.zone_timers:
            elapsed = time.time() - self.zone_timers[zone_id]['start_time']
            self.zone_timers[zone_id]['elapsed'] = elapsed
            return elapsed
        return 0
    
    def stop_timer(self, zone_id):
        """Stop and reset timer when zone exits emergency"""
        if zone_id in self.zone_timers:
            del self.zone_timers[zone_id]
        if zone_id in self.flash_state:
            del self.flash_state[zone_id]
        if zone_id in self.last_flash_toggle:
            del self.last_flash_toggle[zone_id]
    
    def get_elapsed(self, zone_id):
        """Get elapsed time in seconds"""
        if zone_id in self.zone_timers:
            return self.zone_timers[zone_id]['elapsed']
        return 0
    
    def get_formatted_time(self, zone_id):
        """Get formatted time string (MM:SS)"""
        elapsed = self.get_elapsed(zone_id)
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_severity_level(self, zone_id):
        """Get severity level based on elapsed time"""
        from config import TIMER_THRESHOLDS
        
        elapsed = self.get_elapsed(zone_id)
        
        if elapsed >= TIMER_THRESHOLDS['SEVERE']:
            return 'SEVERE'
        elif elapsed >= TIMER_THRESHOLDS['CRITICAL']:
            return 'CRITICAL'
        else:
            return 'WARNING'
    
    def should_flash(self, zone_id):
        """Determine if timer should flash (for SEVERE state)"""
        from config import TIMER_FLASH_INTERVAL
        
        if self.get_severity_level(zone_id) == 'SEVERE':
            current_time = time.time()
            if zone_id in self.last_flash_toggle:
                if current_time - self.last_flash_toggle[zone_id] >= TIMER_FLASH_INTERVAL:
                    self.flash_state[zone_id] = not self.flash_state[zone_id]
                    self.last_flash_toggle[zone_id] = current_time
            return self.flash_state.get(zone_id, True)
        return True  # Always show for non-severe
    
    def get_timer_data(self, zone_id):
        """Get comprehensive timer data for a zone.

        Returns a dict with elapsed, formatted_time, severity, and flash
        if the zone has an active timer; otherwise returns None.
        """
        if zone_id not in self.zone_timers:
            return None
        self.update_timer(zone_id)
        return {
            'elapsed': self.get_elapsed(zone_id),
            'formatted_time': self.get_formatted_time(zone_id),
            'severity': self.get_severity_level(zone_id),
            'flash': self.should_flash(zone_id),
        }

    def get_all_active_timers(self):
        """Get all active emergency timers"""
        return list(self.zone_timers.keys())
    
    def reset_all(self):
        """Reset all timers (e.g., when starting new analysis)"""
        self.zone_timers.clear()
        self.flash_state.clear()
        self.last_flash_toggle.clear()
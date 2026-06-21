import time
import math
import threading
from collections import deque
from PySide6.QtCore import QObject, Signal
from pynput import mouse

class GestureSignals(QObject):
    """
    Signals used to communicate mouse gesture events from the background 
    listener thread to the main PySide6 GUI thread.
    """
    activated = Signal(str)       # Emitted when gesture activates. Argument: "clockwise" or "counter_clockwise"
    deactivated = Signal()        # Emitted when gesture deactivates
    volume_changed = Signal(float) # Emitted on volume adjustment. Argument: volume delta (-1.0 to 1.0)
    debug_status = Signal(str)    # Emitted with debug logs for the settings window

class MouseGestureTracker:
    """
    Tracks global mouse movements and detects deliberate circular gestures.
    Implements a 2-second safety sequence to avoid accidental triggers.
    """
    def __init__(self, signals: GestureSignals):
        self.signals = signals
        
        # Thread safety lock for settings
        self.lock = threading.Lock()
        
        # Default Configuration Settings
        self.enabled = True
        self.activation_delay = 2.0      # Seconds of continuous rotation required to activate
        self.rotation_threshold = 540.0   # Degrees of rotation required to activate (1.5 circles)
        self.sensitivity = 2.0            # Number of rotations required to change volume by 100%
        self.min_radius = 25.0            # Minimum average circle radius (pixels)
        
        # State variables
        self.active = False
        self.active_direction = None      # "clockwise" or "counter_clockwise"
        self.history = deque()            # Holds (x, y, timestamp) tuples
        self.min_move_distance = 12       # Minimum pixels to move before recording a point (reduces noise)
        self.max_history_time = 3.5       # Max time duration of points to keep in memory (seconds)
        self.last_move_time = time.time()
        
        # Active gesture variables
        self.center_x = 0.0
        self.center_y = 0.0
        self.active_radius = 0.0
        self.last_angle = 0.0
        
    def update_settings(self, settings: dict):
        """
        Updates the tracker settings in a thread-safe manner.
        """
        with self.lock:
            self.enabled = settings.get("enabled", self.enabled)
            self.activation_delay = settings.get("activation_delay", self.activation_delay)
            self.rotation_threshold = settings.get("rotation_threshold", self.rotation_threshold)
            self.sensitivity = settings.get("sensitivity", self.sensitivity)
            self.min_radius = settings.get("min_radius", self.min_radius)
            
    def handle_move(self, x, y):
        """
        Called by the global mouse listener whenever the mouse moves.
        """
        with self.lock:
            if not self.enabled:
                self.deactivate()
                return
                
        now = time.time()
        self.last_move_time = now
        
        # 1. Filter out tiny movements (noise / sub-pixel jitter)
        if self.history:
            last_x, last_y, _ = self.history[-1]
            dist = math.hypot(x - last_x, y - last_y)
            if dist < self.min_move_distance:
                return
                
        # 2. Append new coordinate
        self.history.append((x, y, now))
        
        # 3. Clean history of outdated points
        while self.history and (now - self.history[0][2]) > self.max_history_time:
            self.history.popleft()
            
        # 4. Process gesture
        self._process_gesture(x, y, now)
        
    def _process_gesture(self, curr_x, curr_y, now):
        with self.lock:
            activation_delay = self.activation_delay
            rotation_threshold = self.rotation_threshold
            min_radius = self.min_radius
            sensitivity = self.sensitivity
            
        if len(self.history) < 6:
            return
            
        # If we are in the Active control state
        if self.active:
            # Calculate current angle relative to the frozen center of rotation
            dx = curr_x - self.center_x
            dy = curr_y - self.center_y
            r = math.hypot(dx, dy)
            
            # Deactivation checks
            # - If user moves too far from the center (e.g. they broke the circle and moved away)
            # - If user moves too close to the center (radius collapses)
            if r > 400 or r < 12:
                self.signals.debug_status.emit(f"Deactivated: Radius out of bounds ({r:.1f}px)")
                self.deactivate()
                return
                
            current_angle = math.atan2(dy, dx)
            
            # Calculate angle difference
            diff = current_angle - self.last_angle
            # Unwrap diff to [-pi, pi] to handle wrap-around
            if diff > math.pi:
                diff -= 2 * math.pi
            elif diff < -math.pi:
                diff += 2 * math.pi
                
            # Convert to degrees for easier calibration
            diff_deg = math.degrees(diff)
            
            # Volume change is proportional to angle swept
            # sensitivity is number of rotations for 100% volume change
            # One rotation = 360 degrees. 
            # vol_delta = diff_deg / (360 * sensitivity)
            vol_delta = diff_deg / (360.0 * sensitivity)
            
            if abs(vol_delta) > 0.0001:
                self.signals.volume_changed.emit(vol_delta)
                
            self.last_angle = current_angle
            
        # Otherwise, check if we should activate (the 2-second safety sequence)
        else:
            # Filter history to only include points within the activation delay window (e.g. last 2.0s)
            act_points = [p for p in self.history if (now - p[2]) <= activation_delay]
            
            if len(act_points) < 6:
                return
                
            duration = now - act_points[0][2]
            
            # Only evaluate if the continuous movement duration matches/exceeds the required delay
            if duration < activation_delay - 0.1: # Allow a small margin
                return
                
            # Compute centroid of activation points
            xs = [p[0] for p in act_points]
            ys = [p[1] for p in act_points]
            cx = sum(xs) / len(act_points)
            cy = sum(ys) / len(act_points)
            
            # Compute average radius
            radii = [math.hypot(p[0] - cx, p[1] - cy) for p in act_points]
            avg_radius = sum(radii) / len(radii)
            
            # Safety: Must be a reasonable circle size
            if avg_radius < min_radius or avg_radius > 300:
                return
                
            # Compute angles relative to centroid
            angles = [math.atan2(p[1] - cy, p[0] - cx) for p in act_points]
            
            # Unwrap angles to a continuous sequence
            unwrapped = []
            prev_a = angles[0]
            offset = 0.0
            for a in angles:
                diff = a - prev_a
                if diff > math.pi:
                    offset -= 2 * math.pi
                elif diff < -math.pi:
                    offset += 2 * math.pi
                unwrapped.append(a + offset)
                prev_a = a
                
            # Calculate net rotation (final angle - initial angle)
            net_rot = unwrapped[-1] - unwrapped[0]
            net_rot_deg = math.degrees(net_rot)
            
            # Calculate cumulative rotation (total angular distance traveled)
            cum_rot = 0.0
            for i in range(len(unwrapped) - 1):
                cum_rot += abs(unwrapped[i+1] - unwrapped[i])
            cum_rot_deg = math.degrees(cum_rot)
            
            # Check consistency (how clean is the circle?)
            # If they move back and forth, net_rot_deg will be small and cum_rot_deg large.
            # If they rotate cleanly in one direction, consistency will be close to 1.0.
            consistency = 0.0
            if cum_rot_deg > 0:
                consistency = abs(net_rot_deg) / cum_rot_deg
                
            self.signals.debug_status.emit(
                f"Track: Dur={duration:.1f}s | NetRot={net_rot_deg:.1f}° | Const={consistency:.2f} | Rad={avg_radius:.1f}px"
            )
            
            # Activation Criteria:
            # 1. Sustained duration (e.g. 2.0s)
            # 2. Net rotation exceeds threshold (e.g. 540 degrees)
            # 3. Clean circular motion (consistency >= 0.85)
            if abs(net_rot_deg) >= rotation_threshold and consistency >= 0.85:
                self.active = True
                self.center_x = cx
                self.center_y = cy
                self.active_radius = avg_radius
                self.last_angle = math.atan2(curr_y - cy, curr_x - cx)
                
                # Determine direction: Y increases downwards in screen coordinates,
                # so a positive angle change corresponds to Clockwise rotation
                self.active_direction = "clockwise" if net_rot_deg > 0 else "counter_clockwise"
                
                self.signals.debug_status.emit(f"Gesture Activated: {self.active_direction.upper()}")
                self.signals.activated.emit(self.active_direction)
                
    def check_idle(self):
        """
        Called periodically by the main application (e.g., every 100ms) to check
        if the user has stopped moving the mouse. Deactivates if idle.
        """
        now = time.time()
        if self.active and (now - self.last_move_time) > 2.0:
            self.signals.debug_status.emit("Deactivated: Mouse idle (no movement for > 2.0s)")
            self.deactivate()
            
    def deactivate(self):
        """
        Force-deactivates the active gesture state.
        """
        if self.active:
            self.active = False
            self.active_direction = None
            self.history.clear()
            self.signals.deactivated.emit()

class GlobalMouseListener:
    """
    Spawns and manages the background pynput mouse listener thread.
    """
    def __init__(self, tracker: MouseGestureTracker):
        self.tracker = tracker
        self.listener = None
        
    def start(self):
        if self.listener is not None:
            return
            
        self.listener = mouse.Listener(on_move=self._on_move)
        self.listener.daemon = True
        self.listener.start()
        
    def stop(self):
        if self.listener is not None:
            self.listener.stop()
            self.listener.join()
            self.listener = None
            
    def _on_move(self, x, y):
        self.tracker.handle_move(x, y)

import os
import sys

# Redirect stdout and stderr to devnull when running in windowless pythonw.exe mode
# to prevent any crashes when writing logs/exceptions
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import json
import threading
import winsound
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtCore import QTimer, Slot, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QPainterPath, QFont

# Import local modules
from volume import VolumeController
from gesture import GestureSignals, MouseGestureTracker, GlobalMouseListener
from hud import VolumeHUD
from settings_ui import SettingsWindow

CONFIG_FILE = "config.json"

DEFAULT_SETTINGS = {
    "enabled": True,
    "activation_delay": 2.0,          # seconds of circle drawing
    "rotation_threshold": 540.0,      # degrees (1.5 full circles)
    "sensitivity": 2.0,               # rotations for 100% volume change
    "min_radius": 25.0,               # pixels minimum circle size
    "hud_enabled": True,              # visual overlay display
    "hud_theme": "Neon Cyan (Default)",# color profile name
    "sound_enabled": True             # audio clicks
}

def play_audio_feedback(frequency, duration):
    """
    Plays a short beep in a daemon thread so it doesn't block the main GUI thread.
    """
    threading.Thread(
        target=lambda: winsound.Beep(frequency, duration), 
        daemon=True
    ).start()

class MouseGestureApp:
    def __init__(self, qt_app: QApplication):
        self.qt_app = qt_app
        self.settings = DEFAULT_SETTINGS.copy()
        
        # Load custom configuration from file
        self.load_settings()
        
        # Initialize volume controller
        self.volume_controller = VolumeController()
        
        # Initialize GUI components
        self.hud = VolumeHUD()
        self.hud.update_theme(self.settings["hud_theme"])
        
        self.settings_window = None
        
        # Setup tray icon
        self.tray_icon = QSystemTrayIcon(self.create_tray_icon(), self.qt_app)
        self.tray_icon.setToolTip("Mouse Gesture Volume Controller")
        self.setup_tray_menu()
        self.tray_icon.show()
        
        # Setup communication signals
        self.signals = GestureSignals()
        self.signals.activated.connect(self.on_gesture_activated)
        self.signals.deactivated.connect(self.on_gesture_deactivated)
        self.signals.volume_changed.connect(self.on_volume_changed)
        
        # Setup tracker
        self.tracker = MouseGestureTracker(self.signals)
        self.tracker.update_settings(self.settings)
        
        # Setup listener
        self.listener = GlobalMouseListener(self.tracker)
        self.listener.start()
        
        # Periodically check if mouse stopped moving (every 100ms)
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self.tracker.check_idle)
        self.idle_timer.start(100)
        
        # State variables for active volume scaling
        self.activation_volume = 0.5
        self.accumulated_deg = 0.0
        
        # Show a brief, premium notification indicating Volute is active
        from hud import StartupNotification
        self.startup_notification = StartupNotification()
        self.startup_notification.show_notification()
        
    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    file_settings = json.load(f)
                    self.settings.update(file_settings)
            except Exception as e:
                print(f"Error loading config: {e}", file=sys.stderr)
                
    def save_settings(self, new_settings: dict):
        self.settings.update(new_settings)
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}", file=sys.stderr)
            
        # Update tracker settings in background
        self.tracker.update_settings(self.settings)
        
        # Update HUD theme immediately
        self.hud.update_theme(self.settings["hud_theme"])
        
    def create_tray_icon(self) -> QIcon:
        """
        Renders the spiral emoji 🌀 procedurally as a high-resolution QIcon for the tray.
        """
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Use Segoe UI Emoji for high-quality Windows emoji rendering
        font = QFont("Segoe UI Emoji", 36)
        painter.setFont(font)
        
        # Center the spiral emoji 🌀 in the pixmap
        rect = pixmap.rect()
        painter.drawText(rect, Qt.AlignCenter, "🌀")
        
        painter.end()
        return QIcon(pixmap)
        
    def setup_tray_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e24;
                color: #e0e0e6;
                border: 1px solid #363645;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4f4fe5;
                color: #ffffff;
            }
        """)
        
        settings_action = menu.addAction("Settings...")
        settings_action.triggered.connect(self.show_settings)
        
        menu.addSeparator()
        
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(menu)
        
    def show_settings(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.settings, self.save_callback)
            # Connect the tracker signals to the telemetry log inside settings
            self.signals.debug_status.connect(self.settings_window.append_log)
            
        # Re-sync current settings
        self.settings_window.settings = self.settings.copy()
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
        
    def save_callback(self, new_settings: dict):
        self.save_callback(new_settings)
        
    @Slot(str)
    def on_gesture_activated(self, direction: str):
        """
        Triggered when rotation is sustained for > 2 seconds.
        Pulls current system volume and wakes up the HUD.
        """
        self.activation_volume = self.volume_controller.get_volume()
        self.accumulated_deg = 0.0
        
        # Audio feedback: short high beep
        if self.settings["sound_enabled"]:
            play_audio_feedback(2000, 25)
            
        if self.settings["hud_enabled"]:
            self.hud.show_volume(self.activation_volume)
            
    @Slot()
    def on_gesture_deactivated(self):
        """
        Triggered when the user pauses or stops circular movements.
        Dismisses the HUD.
        """
        # Audio feedback: short drop beep
        if self.settings["sound_enabled"]:
            play_audio_feedback(900, 35)
            
        if self.settings["hud_enabled"]:
            self.hud.fade_out()
            
    @Slot(float)
    def on_volume_changed(self, delta_vol: float):
        """
        Triggered when user continues rotating. Adjusts volume relative
        to the initial activation volume based on cumulative degrees.
        """
        # Calculate new volume level
        current_volume = self.volume_controller.get_volume()
        new_vol = current_volume + delta_vol
        new_vol = max(0.0, min(1.0, new_vol))
        
        # Perform adjustment
        self.volume_controller.set_volume(new_vol)
        
        # Audio feedback: soft mechanical tick
        if self.settings["sound_enabled"]:
            play_audio_feedback(1500, 8)
            
        if self.settings["hud_enabled"]:
            self.hud.show_volume(new_vol)
            
    def quit_app(self):
        self.idle_timer.stop()
        self.listener.stop()
        self.hud.close()
        if self.settings_window:
            self.settings_window.close()
        self.qt_app.quit()

def main():
    # Force style for dark mode on Windows
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Run application logic
    gesture_app = MouseGestureApp(app)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

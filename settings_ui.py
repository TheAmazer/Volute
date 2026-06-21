from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QCheckBox, QComboBox, QPushButton, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QIcon

class SettingsWindow(QWidget):
    """
    Sleek, dark-themed configuration GUI for the Mouse Gesture Volume Control app.
    Provides sliders, dropdowns, and checkboxes to fine-tune the tracking math
    and visual overlay themes. Includes a live mathematical telemetry log.
    """
    def __init__(self, current_settings: dict, save_callback):
        super().__init__()
        
        self.settings = current_settings.copy()
        self.save_callback = save_callback
        
        self.setWindowTitle("Mouse Gesture Volume Settings")
        self.setFixedSize(560, 780)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # Apply dark premium QSS style
        self.setStyleSheet("""
            QWidget {
                background-color: #16161a;
                color: #e2e2ea;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QLabel {
                color: #e2e2ea;
            }
            QLabel#header_title {
                color: #00f2fe;
                font-size: 18px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QLabel#header_subtitle {
                color: #888899;
                font-size: 11px;
            }
            QGroupBox {
                border: 1px solid #2e2e38;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 15px;
                font-weight: 600;
                color: #00f2fe;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 0 5px;
            }
            /* Custom styled sliders */
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #2b2b36;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2fe, stop:1 #4f4fe5);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #4f4fe5;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #00f2fe;
                border-color: #ffffff;
            }
            /* Buttons styling */
            QPushButton {
                background-color: #24242d;
                border: 1px solid #363645;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #2b2b36;
                border-color: #00f2fe;
            }
            QPushButton#save_btn {
                background-color: #4f4fe5;
                border: 1px solid #00f2fe;
            }
            QPushButton#save_btn:hover {
                background-color: #00f2fe;
                color: #16161a;
            }
            QPushButton#reset_btn:hover {
                border-color: #ff5f6d;
                color: #ff5f6d;
            }
            /* Dropdowns */
            QComboBox {
                background-color: #24242d;
                border: 1px solid #363645;
                border-radius: 6px;
                padding: 5px;
                color: #ffffff;
            }
            QComboBox:on {
                border-color: #00f2fe;
            }
            QComboBox QAbstractItemView {
                background-color: #24242d;
                border: 1px solid #363645;
                selection-background-color: #4f4fe5;
                selection-color: #ffffff;
            }
            /* Custom styled checkboxes */
            QCheckBox {
                spacing: 8px;
                color: #e2e2ea;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #4d4d5d;
                border-radius: 4px;
                background-color: #24242d;
            }
            QCheckBox::indicator:hover {
                border-color: #00f2fe;
                background-color: #2d2d3b;
            }
            QCheckBox::indicator:checked {
                background-color: #00f2fe;
                border: 3px solid #16161a;
            }
            /* Text logger */
            QTextEdit#log_console {
                background-color: #0e0e11;
                border: 1px solid #22222b;
                border-radius: 8px;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 11px;
                color: #8892b0;
            }
        """)
        
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # --- Header Section ---
        header_layout = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        
        title_label = QLabel("GESTURE VOLUME ENGINE", self)
        title_label.setObjectName("header_title")
        subtitle_label = QLabel("Tune tracking sensitivity and interface aesthetics", self)
        subtitle_label.setObjectName("header_subtitle")
        
        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(subtitle_label)
        header_layout.addLayout(header_text_layout)
        
        # Global Enable/Disable State
        self.enable_checkbox = QCheckBox("Gesture Engine Active", self)
        self.enable_checkbox.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 13px;")
        self.enable_checkbox.setChecked(self.settings.get("enabled", True))
        self.enable_checkbox.toggled.connect(self._on_enable_toggled)
        header_layout.addWidget(self.enable_checkbox, 0, Qt.AlignVCenter | Qt.AlignRight)
        
        main_layout.addLayout(header_layout)
        
        # --- Group Box: Engine Sensitivity Settings ---
        engine_group = QGroupBox("1. Gesture Tracking Settings", self)
        engine_layout = QVBoxLayout(engine_group)
        engine_layout.setContentsMargins(15, 20, 15, 15)
        engine_layout.setSpacing(12)
        
        # Slider: Activation Delay (Seconds of continuous circle before trigger)
        self.delay_slider, self.delay_label = self._create_slider_row(
            engine_layout, "Activation Delay", "Time moving in a circle before adjusting volume.",
            10, 40, int(self.settings.get("activation_delay", 2.0) * 10), "s", divisor=10.0
        )
        self.delay_slider.valueChanged.connect(self._on_delay_changed)
        
        # Slider: Required Rotation Degrees (Initial circular turn required)
        self.rotation_slider, self.rotation_label = self._create_slider_row(
            engine_layout, "Activation Rotation", "Degrees of circle required to trigger (360° = 1 loop).",
            180, 720, int(self.settings.get("rotation_threshold", 540.0)), "°", step=45
        )
        self.rotation_slider.valueChanged.connect(self._on_rotation_changed)
        
        # Slider: Volume Sensitivity (Rotations for 100% Volume change)
        self.speed_slider, self.speed_label = self._create_slider_row(
            engine_layout, "Scroll Speed", "Number of rotations required to change volume 0% to 100%.",
            5, 50, int(self.settings.get("sensitivity", 2.0) * 10), " rotations", divisor=10.0
        )
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        
        # Slider: Minimum Circle Radius (Ignore small circles / fidgeting)
        self.radius_slider, self.radius_label = self._create_slider_row(
            engine_layout, "Min Circle Radius", "Minimum size of circular gesture in pixels.",
            15, 80, int(self.settings.get("min_radius", 25.0)), "px"
        )
        self.radius_slider.valueChanged.connect(self._on_radius_changed)
        
        main_layout.addWidget(engine_group)
        
        # --- Group Box: Interface & Themes ---
        ui_group = QGroupBox("2. Visuals & Audio Feedback", self)
        ui_layout = QVBoxLayout(ui_group)
        ui_layout.setContentsMargins(15, 20, 15, 15)
        ui_layout.setSpacing(12)
        
        # HUD theme selection
        theme_row = QHBoxLayout()
        theme_title_layout = QVBoxLayout()
        theme_label = QLabel("Overlay HUD Color Theme", self)
        theme_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        theme_desc = QLabel("Color palette for the translucent volume ring.", self)
        theme_desc.setStyleSheet("color: #888899; font-size: 11px;")
        theme_title_layout.addWidget(theme_label)
        theme_title_layout.addWidget(theme_desc)
        theme_row.addLayout(theme_title_layout)
        
        self.theme_combo = QComboBox(self)
        self.theme_combo.addItems([
            "Neon Cyan (Default)", 
            "Amber Sunset", 
            "Emerald Glow", 
            "Magenta Flare"
        ])
        self.theme_combo.setCurrentText(self.settings.get("hud_theme", "Neon Cyan (Default)"))
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_combo, 0, Qt.AlignVCenter | Qt.AlignRight)
        ui_layout.addLayout(theme_row)
        
        # Checkboxes for HUD Toggle and Click Sounds
        checkboxes_layout = QHBoxLayout()
        
        self.hud_checkbox = QCheckBox("Show Visual HUD Ring", self)
        self.hud_checkbox.setChecked(self.settings.get("hud_enabled", True))
        self.hud_checkbox.toggled.connect(self._on_hud_toggled)
        checkboxes_layout.addWidget(self.hud_checkbox)
        
        self.sound_checkbox = QCheckBox("Enable Click Audio", self)
        self.sound_checkbox.setChecked(self.settings.get("sound_enabled", True))
        self.sound_checkbox.toggled.connect(self._on_sound_toggled)
        checkboxes_layout.addWidget(self.sound_checkbox)
        
        ui_layout.addLayout(checkboxes_layout)
        
        main_layout.addWidget(ui_group)
        
        # --- Live Mathematical Telemetry Console ---
        console_group = QGroupBox("Live Tracking Telemetry", self)
        console_layout = QVBoxLayout(console_group)
        console_layout.setContentsMargins(10, 15, 10, 10)
        
        self.log_console = QTextEdit(self)
        self.log_console.setObjectName("log_console")
        self.log_console.setReadOnly(True)
        self.log_console.setPlaceholderText("Telemetry output will stream here in real-time when mouse moves...")
        self.log_console.setMinimumHeight(100)
        console_layout.addWidget(self.log_console)
        
        main_layout.addWidget(console_group)
        
        # --- Action Buttons Section ---
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset Defaults", self)
        reset_btn.setObjectName("reset_btn")
        reset_btn.clicked.connect(self._on_reset_clicked)
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.close)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Apply Settings", self)
        save_btn.setObjectName("save_btn")
        save_btn.clicked.connect(self._on_save_clicked)
        buttons_layout.addWidget(save_btn)
        
        main_layout.addLayout(buttons_layout)
        
    def _create_slider_row(self, layout, title, desc, min_val, max_val, curr_val, suffix, divisor=1.0, step=1):
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 2, 0, 2)
        
        # Combine title and description into a single RichText QLabel to prevent vertical overlap
        label_text = f"<b>{title}</b><br><span style='color: #8c8c9e; font-size: 11px;'>{desc}</span>"
        label = QLabel(label_text, self)
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        row_layout.addWidget(label)
        
        slider_val_layout = QHBoxLayout()
        slider_val_layout.setSpacing(10)
        
        slider = QSlider(Qt.Horizontal, self)
        slider.setRange(min_val, max_val)
        slider.setSingleStep(step)
        slider.setValue(curr_val)
        slider.setFixedWidth(160)
        slider_val_layout.addWidget(slider)
        
        val_disp = curr_val / divisor if divisor > 1.0 else curr_val
        val_label = QLabel(f"{val_disp}{suffix}", self)
        val_label.setFixedWidth(80)
        val_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        slider_val_layout.addWidget(val_label)
        
        row_layout.addLayout(slider_val_layout)
        layout.addLayout(row_layout)
        
        return slider, val_label
        
    # --- Settings Change Sliders and Events ---
    def _on_enable_toggled(self, checked):
        self.settings["enabled"] = checked
        
    def _on_hud_toggled(self, checked):
        self.settings["hud_enabled"] = checked
        
    def _on_sound_toggled(self, checked):
        self.settings["sound_enabled"] = checked
        
    def _on_theme_changed(self, text):
        self.settings["hud_theme"] = text
        
    def _on_delay_changed(self, val):
        sec = val / 10.0
        self.delay_label.setText(f"{sec:.1f}s")
        self.settings["activation_delay"] = sec
        
    def _on_rotation_changed(self, val):
        self.rotation_label.setText(f"{val}°")
        self.settings["rotation_threshold"] = float(val)
        
    def _on_speed_changed(self, val):
        rot = val / 10.0
        self.speed_label.setText(f"{rot:.1f} rotations")
        self.settings["sensitivity"] = rot
        
    def _on_radius_changed(self, val):
        self.radius_label.setText(f"{val}px")
        self.settings["min_radius"] = float(val)
        
    @Slot(str)
    def append_log(self, text: str):
        """
        Receives real-time telemetry from the tracker thread and prints it.
        Prunes old lines to prevent infinite memory usage.
        """
        self.log_console.append(text)
        # Keep only the last 150 lines in console
        doc = self.log_console.document()
        if doc.blockCount() > 150:
            cursor = self.log_console.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar() # removes the newline
            
    def _on_reset_clicked(self):
        # Reset GUI controls to default configuration
        self.enable_checkbox.setChecked(True)
        self.hud_checkbox.setChecked(True)
        self.sound_checkbox.setChecked(True)
        
        self.delay_slider.setValue(20)  # 2.0s
        self.rotation_slider.setValue(540) # 540°
        self.speed_slider.setValue(20) # 2.0 rotations
        self.radius_slider.setValue(25) # 25px
        self.theme_combo.setCurrentText("Neon Cyan (Default)")
        
    def _on_save_clicked(self):
        self.save_callback(self.settings)
        self.close()

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient, QFont
from PySide6.QtCore import Property

# Color theme profiles for visual customization
THEME_PALETTES = {
    "Neon Cyan (Default)": {
        "start": QColor(0, 242, 254),       # Neon Cyan
        "end": QColor(79, 79, 229),         # Indigo
        "glow": QColor(0, 242, 254, 80)
    },
    "Amber Sunset": {
        "start": QColor(255, 95, 109),      # Coral Pink
        "end": QColor(255, 195, 113),       # Sunset Yellow
        "glow": QColor(255, 95, 109, 80)
    },
    "Emerald Glow": {
        "start": QColor(17, 224, 137),      # Bright Emerald
        "end": QColor(0, 168, 255),         # Electric Blue
        "glow": QColor(17, 224, 137, 80)
    },
    "Magenta Flare": {
        "start": QColor(240, 46, 170),      # Hot Magenta
        "end": QColor(255, 95, 109),        # Coral Pink
        "glow": QColor(240, 46, 170, 80)
    }
}

class CircularProgressBar(QWidget):
    """
    Custom circular progress bar drawn using QPainter.
    Supports gradient coloring, perfect text centering, and smooth,
    flowing value transition animations (Apple-style).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.5  # internal displayed value
        self.target_value = 0.5
        self.theme_name = "Neon Cyan (Default)"
        self.setMinimumSize(160, 160)
        
        # Apple-style smooth ease-out value animation
        self.anim = QPropertyAnimation(self, b"display_value")
        self.anim.setDuration(150)  # 150ms for responsive but buttery-smooth flow
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        
    def get_display_value(self) -> float:
        return self._value
        
    def set_display_value(self, val: float):
        self._value = val
        self.update()
        
    # Expose displayed value as a Qt Property for QPropertyAnimation
    display_value = Property(float, get_display_value, set_display_value)
    
    def set_value(self, val: float, animate=True):
        val = max(0.0, min(1.0, val))
        self.target_value = val
        
        if animate:
            self.anim.stop()
            self.anim.setStartValue(self._value)
            self.anim.setEndValue(val)
            self.anim.start()
        else:
            self.anim.stop()
            self.set_display_value(val)
        
    def set_theme(self, theme_name: str):
        if theme_name in THEME_PALETTES:
            self.theme_name = theme_name
            self.update()
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        # Leave padding for outline thickness
        size = min(width, height) - 20
        rect = QRectF((width - size) / 2, (height - size) / 2, size, size)
        
        # 1. Draw background track circle
        bg_pen = QPen(QColor(50, 50, 65, 80), 8)
        painter.setPen(bg_pen)
        painter.drawEllipse(rect)
        
        # 2. Draw progress arc (using current animated displayed value)
        start_angle = 90 * 16
        span_angle = int(-self._value * 360 * 16)
        
        palette = THEME_PALETTES.get(self.theme_name, THEME_PALETTES["Neon Cyan (Default)"])
        
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, palette["start"])
        gradient.setColorAt(1.0, palette["end"])
        
        prog_pen = QPen(QBrush(gradient), 8)
        prog_pen.setCapStyle(Qt.RoundCap)  # Clean rounded caps
        painter.setPen(prog_pen)
        painter.drawArc(rect, start_angle, span_angle)
        
        # 3. Draw volume text in center (using _value to count up/down smoothly)
        text = f"{int(self._value * 100)}%"
        painter.setPen(QColor(255, 255, 255))
        
        # Bold, high-end sans-serif font
        font = QFont("Segoe UI", 24, QFont.Bold)
        painter.setFont(font)
        
        # Draw centered inside the circular track rect (perfect centering)
        painter.drawText(rect, Qt.AlignCenter, text)


class VolumeHUD(QWidget):
    """
    Translucent glassmorphic overlay widget that displays system volume changes.
    Stays on top, is click-through, and centers on the current mouse screen.
    """
    def __init__(self):
        super().__init__()
        
        self.theme_name = "Neon Cyan (Default)"
        
        # Window attributes: Frameless, translucent, click-through, stays-on-top
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.WindowTransparentForInput |
            Qt.Tool  # Hides from Windows Alt-Tab window list
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(240, 260)
        
        # Setup layouts
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setAlignment(Qt.AlignCenter)
        
        # Main glassmorphic panel container
        self.container = QWidget(self)
        self.container.setObjectName("Container")
        self.container.setStyleSheet("""
            QWidget#Container {
                background-color: rgba(18, 18, 25, 210);
                border: 1px solid rgba(255, 255, 255, 15);
                border-radius: 28px;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(10, 20, 10, 20)
        container_layout.setAlignment(Qt.AlignCenter)
        
        # Header Label (Icon + State)
        self.icon_label = QLabel(self.container)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("color: #a5a5b5; font-size: 13px; font-weight: 600; letter-spacing: 1px;")
        self.icon_label.setText("VOLUME")
        container_layout.addWidget(self.icon_label)
        
        # Circular Progress Bar
        self.progress_bar = CircularProgressBar(self.container)
        container_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.container)
        
        # Glowing shadow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(30)
        self.shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(self.shadow)
        
        self.update_theme(self.theme_name)
        
        # Setup opacity fade-in/out animations
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.OutQuad)
        
        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.fade_out)
        
        self.setWindowOpacity(0.0)
        self.is_visible = False
        
    def update_theme(self, theme_name: str):
        """
        Updates the visual color palette and shadow glow of the HUD.
        """
        self.theme_name = theme_name
        self.progress_bar.set_theme(theme_name)
        
        palette = THEME_PALETTES.get(theme_name, THEME_PALETTES["Neon Cyan (Default)"])
        self.shadow.setColor(palette["glow"])
        
    def show_volume(self, val: float):
        """
        Updates the progress ring value, changes speaker icons, 
        centers on the cursor screen, and triggers a smooth fade-in.
        """
        self.progress_bar.set_value(val, animate=self.is_visible)
        
        # Set dynamic icon indicator
        vol_pct = int(val * 100)
        if vol_pct == 0:
            self.icon_label.setText("MUTED 🔇")
        elif vol_pct < 33:
            self.icon_label.setText("VOLUME 🔈")
        elif vol_pct < 66:
            self.icon_label.setText("VOLUME 🔉")
        else:
            self.icon_label.setText("VOLUME 🔊")
            
        # Dynamically center on the screen housing the cursor
        self.center_on_screen()
        
        if not self.is_visible:
            self.show()
            self.fade_animation.stop()
            self.fade_animation.setStartValue(self.windowOpacity())
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.start()
            self.is_visible = True
            
        # Reset hide timer (auto-dismiss after 1.5 seconds of silence)
        self.hide_timer.start(1500)
        
    def fade_out(self):
        if self.is_visible:
            self.fade_animation.stop()
            self.fade_animation.setStartValue(self.windowOpacity())
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.finished.connect(self.on_fade_out_finished)
            self.fade_animation.start()
            self.is_visible = False
            
    def on_fade_out_finished(self):
        try:
            self.fade_animation.finished.disconnect(self.on_fade_out_finished)
        except RuntimeError:
            pass
        if not self.is_visible:
            self.hide()
            
    def center_on_screen(self):
        from PySide6.QtGui import QCursor, QGuiApplication
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos)
        if not screen:
            screen = QGuiApplication.primaryScreen()
            
        geom = screen.geometry()
        x = geom.x() + (geom.width() - self.width()) // 2
        y = geom.y() + (geom.height() - self.height()) // 2
        self.move(x, y)

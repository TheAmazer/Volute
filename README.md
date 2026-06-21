# Volute 🌀

**Volute** is a Windows system tray utility that tracks mouse movement in the background and adjusts the system volume when a clockwise or counter-clockwise rotation is deliberately performed and sustained for more than 2 seconds (our safety sequence).

The name **Volute** is a double-meaning: it represents the circular, spiral-like mouse gesture (*volute* literally means "a spiral curve or scroll"), and it begins with **Vol** (Volume).

## Demonstration & Visuals

*(Below are placeholders for future screenshots showing the visual HUD themes and settings layout)*

| Settings Control Panel | Translucent HUD Overlay |
| :---: | :---: |
| ![Settings Panel Placeholder](https://via.placeholder.com/400x560.png?text=Volute+Settings+Panel) | ![HUD Ring Placeholder](https://via.placeholder.com/300x300.png?text=Volute+HUD+Ring) |

*The overlay HUD features neon-glowing color gradients that sweep smoothly as you rotate the mouse.*

## Features

- **2-Second Safety Sequence**: Prevents accidental volume adjustments during normal browsing, gaming, or point-and-click work. The gesture must be sustained continuously for at least 2 seconds to activate.
- **Clockwise Rotation**: Increases master system volume.
- **Counter-Clockwise Rotation**: Decreases master system volume.
- **Tactile Audio Feedback**: Emits subtle, non-blocking click sounds (similar to mechanical encoder clicks) when adjusting, and distinct startup/shutdown chirps when activating or deactivating.
- **Glassmorphic HUD Overlay**: Displays a translucent, glowing visual ring at the center of the active monitor indicating the current volume percentage. Fades out smoothly after 1.5 seconds of inactivity.
- **Aesthetic Settings Panel**: Styled in premium dark mode. Allows adjusting activation delay, required rotation, scroll speed, minimum radius, HUD themes, and includes a live mathematical telemetry log.

## Visual Themes

You can customize the HUD overlay with the following themes via the Settings window:
- **Neon Cyan (Default)**: Bright cyan to deep blue gradient.
- **Amber Sunset**: Coral pink to warm orange gradient.
- **Emerald Glow**: Neon green to ocean blue gradient.
- **Magenta Flare**: Hot pink to coral gradient.

## Requirements

The app is built for Windows and relies on the following Python packages:
- `PySide6` (for GUI, tray, HUD overlay, and settings)
- `pynput` (for global mouse hook)
- `pycaw` & `comtypes` (for Windows master audio API control)

## Setup & Running

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the Application**:
   ```bash
   pythonw app.pyw
   ```
3. **Use the Application**:
   - The application will launch quietly in the system tray.
   - To open settings, right-click the tray icon (cyan loop with mouse cursor) and select **Settings...**.
   - To use the gesture: Draw a circle continuously for 2 seconds. Once activated (you will hear a click and see the HUD fade in), continue rotating to adjust volume. Stop moving the mouse or move in a straight line to exit.

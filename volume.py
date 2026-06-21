import sys
from ctypes import cast, POINTER

# On Windows, we use pycaw. On other platforms (if any, though workspace is Windows),
# we can stub it to avoid crashes during development/testing.
try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    WINDOWS_AUDIO_AVAILABLE = True
except ImportError:
    WINDOWS_AUDIO_AVAILABLE = False

class VolumeController:
    """
    Handles retrieval and modification of the Windows master system volume
    using the Core Audio Windows API via pycaw.
    """
    def __init__(self):
        self.volume = None
        self._mock_volume = 0.5  # Fallback for non-Windows or if initialization fails
        if WINDOWS_AUDIO_AVAILABLE:
            self.initialize_audio()
            
    def initialize_audio(self):
        if not WINDOWS_AUDIO_AVAILABLE:
            return False
        try:
            speakers = AudioUtilities.GetSpeakers()
            if not speakers:
                return False
            
            # Support both old and new pycaw versions
            if hasattr(speakers, "EndpointVolume"):
                self.volume = speakers.EndpointVolume
            else:
                interface = speakers.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            return True
        except Exception as e:
            print(f"[VolumeController] Error initializing Windows core audio: {e}", file=sys.stderr)
            self.volume = None
            return False
            
    def get_volume(self) -> float:
        """
        Returns the master volume level as a scalar float between 0.0 and 1.0.
        """
        if not WINDOWS_AUDIO_AVAILABLE:
            return self._mock_volume
            
        if not self.volume:
            self.initialize_audio()
            
        if self.volume:
            try:
                return self.volume.GetMasterVolumeLevelScalar()
            except Exception as e:
                print(f"[VolumeController] Exception getting volume, re-initializing: {e}", file=sys.stderr)
                if self.initialize_audio():
                    try:
                        return self.volume.GetMasterVolumeLevelScalar()
                    except Exception:
                        pass
        return self._mock_volume
        
    def set_volume(self, value: float) -> bool:
        """
        Sets the master volume level to a scalar float between 0.0 and 1.0.
        Automatically unmutes the audio device if the value is > 0.0.
        """
        # Clamp value to [0.0, 1.0]
        value = max(0.0, min(1.0, value))
        self._mock_volume = value
        
        if not WINDOWS_AUDIO_AVAILABLE:
            return True
            
        if not self.volume:
            self.initialize_audio()
            
        if self.volume:
            try:
                self.volume.SetMasterVolumeLevelScalar(value, None)
                # If volume is > 0 and system is muted, unmute it
                if value > 0.0 and self.volume.GetMute():
                    self.volume.SetMute(0, None)
                return True
            except Exception as e:
                print(f"[VolumeController] Exception setting volume, re-initializing: {e}", file=sys.stderr)
                if self.initialize_audio():
                    try:
                        self.volume.SetMasterVolumeLevelScalar(value, None)
                        if value > 0.0 and self.volume.GetMute():
                            self.volume.SetMute(0, None)
                        return True
                    except Exception:
                        pass
        return False

    def is_muted(self) -> bool:
        """
        Checks if the master volume is muted.
        """
        if not WINDOWS_AUDIO_AVAILABLE or not self.volume:
            return False
        try:
            return bool(self.volume.GetMute())
        except Exception:
            return False

    def toggle_mute(self) -> bool:
        """
        Toggles the mute state of the master audio device.
        """
        if not WINDOWS_AUDIO_AVAILABLE or not self.volume:
            return False
        try:
            current_mute = self.volume.GetMute()
            self.volume.SetMute(1 - current_mute, None)
            return True
        except Exception:
            return False

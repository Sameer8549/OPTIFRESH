import urllib.parse
import numpy as np
import io
from scipy.io.wavfile import write

try:
    from gTTS import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("Warning: gTTS module not found. Voice features disabled.")

class NotificationEngine:
    def generate_voice_report(self, item_name, condition, confidence):
        """
        Generates a Smart AI Voice Report using Google TTS.
        """
        if not GTTS_AVAILABLE:
            return self.generate_alert_sound("high").getvalue()

        try:
            tone = "Warning." if "Rot" in condition or "Discard" in condition else "System Standard."
            text = f"{tone} Detected {item_name}. Freshness is {confidence:.0f} percent. {condition}."
            
            tts = gTTS(text=text, lang='en', tld='co.in') # British/Indian English
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            return fp.getvalue()
        except Exception as e:
            # Fallback to simple beep if no internet for TTS
            return self.generate_alert_sound("high").getvalue()

    def generate_alert_sound(self, severity="high"):
        """
        Generates a synthetic audio alert (Sine wave beep) as bytes.
        Returns: BytesIO object of a .wav file.
        """
        sample_rate = 44100
        duration = 1.0 # seconds
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # High Pitch beep for Danger, Low for Info
        freq = 880 if severity == "high" else 440
        
        # Generate Sine Wave
        note = np.sin(freq * t * 2 * np.pi)
        
        # Add a "Siren" modulation for high severity
        if severity == "high":
            modulation = np.sin(10 * t * 2 * np.pi)
            note = np.sin((freq + modulation * 100) * t * 2 * np.pi)
            
        # Ensure 16-bit PCM
        audio = (note * 32767).astype(np.int16)
        
        byte_io = io.BytesIO()
        write(byte_io, sample_rate, audio)
        return byte_io

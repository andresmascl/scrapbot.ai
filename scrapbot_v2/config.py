"""
Configuration for scrapbot_v2.
Centralized settings with sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# --- AUDIO SETTINGS ---
AUDIO_RATE = 16000  # Sample rate (Hz)
CHANNELS = 1  # Mono audio
FRAME_SIZE = 1024  # Bytes per frame
READ_CHUNK_SIZE = FRAME_SIZE  # Chunk size for stream reading

# --- WAKE WORD DETECTION ---
WAKE_KEY = "hey_mycroft"
WAKE_THRESHOLD = float(os.getenv("WAKE_THRESHOLD", "0.7"))
WAKE_COOLDOWN_SEC = 3.0  # Cooldown after detection
WAKE_SOUND_PATH = "/app/wakeword-confirmed.mp3"

# --- VOICE ACTIVITY DETECTION ---
VAD_THRESHOLD = 0.5  # Speech detection threshold
SILENCE_SECONDS = 1.5  # Seconds of silence to end recording
SILENCE_THRESHOLD_MS = int(SILENCE_SECONDS * 1000)

# --- TTS & REARM ---
TTS_REARM_DELAY_SEC = float(os.getenv("TTS_REARM_DELAY_SEC", "5.0"))  # Delay after TTS
STREAM_DRAIN_SEC = 0.5  # Time to drain stream buffer

# --- GCP / GEMINI API ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash-live")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- DEBUG / LOGGING ---
ENABLE_VOLUME_BAR = os.getenv("ENABLE_VOLUME_BAR", "0") == "1"

# --- TIMEOUTS ---
NO_SPEECH_TIMEOUT_SEC = 5.0  # Timeout if no speech detected
MAX_RECORDING_SEC = 30.0  # Maximum recording duration

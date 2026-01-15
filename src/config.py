import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# --- AUDIO ---
AUDIO_RATE = 16000
CHANNELS = 1
FRAME_SIZE = 1024
AUDIO_DEVICE_INDEX = os.getenv("AUDIO_DEVICE_INDEX")
if AUDIO_DEVICE_INDEX:
    try:
        AUDIO_DEVICE_INDEX = int(AUDIO_DEVICE_INDEX)
    except ValueError:
        AUDIO_DEVICE_INDEX = None

# --- LOGGING ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# --- WAKE WORD ---
WAKE_KEY = os.getenv("WAKE_KEY", "hey_mycroft")
WAKE_THRESHOLD = float(os.getenv("WAKE_THRESHOLD", "0.7"))
VAD_THRESHOLD = float(os.getenv("VAD_THRESHOLD", "0.5"))
SILENCE_SECONDS = float(os.getenv("SILENCE_SECONDS", "1.0"))
TTS_REARM_DELAY_SEC = float(os.getenv("TTS_REARM_DELAY_SEC", "5.0"))

# --- REASONER ---
COMMAND_TIMEOUT = float(os.getenv("COMMAND_TIMEOUT", "3.0"))

# --- BRAVE / PLAYER ---
BRAVE_BINARY = os.getenv("BRAVE_BINARY", "/usr/bin/brave-browser")
BRAVE_USER_DATA_DIR = os.getenv("BRAVE_USER_DATA_DIR")
BRAVE_PROFILE = os.getenv("BRAVE_PROFILE", "Profile 2")
WS_PORT = int(os.getenv("WS_PORT", "8765"))
WS_HOST = os.getenv("WS_HOST", "127.0.0.1")

# --- GCP ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash")
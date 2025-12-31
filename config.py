import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# --- AUDIO ---
AUDIO_RATE = 16000
CHANNELS = 1
FRAME_SIZE = 1024

# --- WAKE WORD ---
WAKE_KEY = "hey_mycroft"
WAKE_THRESHOLD = float(os.getenv("WAKE_THRESHOLD", "0.7"))
VAD_THRESHOLD = 0.5
SILENCE_SECONDS = 1
TTS_REARM_DELAY_SEC = float(os.getenv("TTS_REARM_DELAY_SEC", "5.0"))

# --- GCP ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash")
LIVE_API_VOICE = os.getenv("LIVE_API_VOICE", "Aoede")

# --- Brave / Browser ---
BROWSER_BINARY_PATH = os.getenv("BROWSER_BINARY_PATH")
BRAVE_PROFILE_PATH = os.getenv("BRAVE_PROFILE_PATH")

if not BROWSER_BINARY_PATH:
    raise RuntimeError("Missing BROWSER_BINARY_PATH in .env")

if not BRAVE_PROFILE_PATH:
    raise RuntimeError("Missing BRAVE_PROFILE_PATH in .env")

SYSTEM_INSTRUCTION = (
    "You are Scrapbot, a helpful robotic assistant. "
    "Respond concisely and execute browser actions when required."
)

import os 
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# --- AUDIO & LISTENER ---
AUDIO_RATE = 16000
CHANNELS = 1
FRAME_SIZE = 1024

# --- WAKE WORD & VAD ---
WAKE_KEY = "hey_mycroft"
WAKE_THRESHOLD = float(os.getenv("WAKE_THRESHOLD", "0.7"))  # Increased from 0.6 to reduce false positives
VAD_THRESHOLD = 0.5
SILENCE_SECONDS = 1
# Delay after TTS to prevent audio feedback/echo from retriggering wake word
TTS_REARM_DELAY_SEC = float(os.getenv("TTS_REARM_DELAY_SEC", "5.0"))  # Increased from 3.0 to 5.0

# --- GCP / LIVE API ---
# These now pull from the organized .env via Docker
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash-live")
LIVE_API_VOICE = os.getenv("LIVE_API_VOICE", "Aoede")

SYSTEM_INSTRUCTION = (
    "You are Scrapbot, a helpful robotic assistant. Respond in a friendly, "
    "concise manner. If a user asks to move the robot, use your tools."
)
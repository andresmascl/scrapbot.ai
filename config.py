"""Configuration for Scrapbot.ai"""
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024

# Wake word settings
WAKE_WORD = "hey_mycroft"
WAKE_THRESHOLD = float(os.getenv("WAKE_THRESHOLD", "0.7"))

# VAD settings
VAD_THRESHOLD = 0.5
SILENCE_DURATION_MS = 1000  # 1 second of silence to stop recording
MAX_RECORDING_SEC = 30

# Google Cloud settings
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash-exp")

# Paths
WAKE_SOUND_PATH = "/app/wakeword-confirmed.mp3"
PROMPT_PATH = "PROMPT.md"

# Session management
SESSION_TIMEOUT_HOURS = 7

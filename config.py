# config.py
import os 
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from google.cloud import speech_v2 as speech
from google.api_core.client_options import ClientOptions
from google.oauth2 import service_account

# 1. Setup Paths and Load Env
load_dotenv(find_dotenv())

# ---------------------------------------------------------
# 2. AUDIO & LISTENER SETTINGS (Restored)
# ---------------------------------------------------------
AUDIO_RATE = 16000
CHANNELS = 1
FRAME_SIZE = 1536

# Wake word settings
WAKE_KEY = "hey_mycroft"
WAKE_THRESHOLD = 0.6
WAKE_RESET_THRESHOLD = 0.2
WAKE_COOLDOWN_SEC = 3.0

# VAD (Voice Activity Detection) settings
VAD_MODE = 2
SILENCE_SECONDS = 1
MIN_SPEECH_SECONDS = 0.3
VAD_THRESHOLD = 0.5

# ---------------------------------------------------------
# 3. GOOGLE CLOUD / REASONER SETTINGS
# ---------------------------------------------------------
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_MODEL_NAME")

# ---------------------------------------------------------
# 4. INITIALIZE CLIENTS (Singleton Pattern)
# ---------------------------------------------------------
try:
    # Chirp 2 MUST use the regional endpoint: e.g., us-central1-speech.googleapis.com
    api_endpoint = f"{REGION}-speech.googleapis.com"
    client_options = ClientOptions(api_endpoint=api_endpoint)
    
    # Explicitly load credentials to avoid gRPC discovery hangs
    credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_JSON)

    speech_client = speech.SpeechClient(
        credentials=credentials,
        client_options=client_options
    )
    print(f"✅ SpeechClient V2 initialized for {api_endpoint}")
except Exception as e:
    print(f"❌ Failed to load SpeechClient V2: {e}")
    raise
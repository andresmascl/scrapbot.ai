from dotenv import load_dotenv
from pathlib import Path
import os

from google.cloud import speech_v1p1beta1 as speech
import vertexai
from vertexai.generative_models import GenerativeModel

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# --------------------
# Required env vars
# --------------------
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_MODEL_NAME")

# --------------------
# Validation (fail fast)
# --------------------
missing = [
    name for name, value in {
        "GOOGLE_APPLICATION_CREDENTIALS": GOOGLE_CREDENTIALS_JSON,
        "GCP_PROJECT_ID": PROJECT_ID,
        "VERTEX_MODEL_NAME": MODEL_NAME,
    }.items()
    if not value
]

if missing:
    raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

# --------------------
# Clients
# --------------------
speech_client = speech.SpeechClient.from_service_account_file(
    GOOGLE_CREDENTIALS_JSON
)

vertexai.init(
    project=PROJECT_ID,
    location=REGION,
)
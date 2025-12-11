import openai
import os
import numpy as np
import soundfile as sf
from dotenv import load_dotenv
from computer_use import run_claude

load_dotenv("utilities/.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

def read_audio_npy(path):
    return np.load(path).astype("float32")

def transcribe_and_forward(path):
    print("🔍 Transcribing with Whisper...")

    audio = read_audio_npy(path)
    wav_path = "temp.wav"
    sf.write(wav_path, audio, 16000)

    client = openai.OpenAI()

    with open(wav_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-tts",
            file=f
        )

    text = transcript.text
    print("📝 Whisper text:", text)
    run_claude(text)
import sounddevice as sd
import numpy as np
import soundfile as sf
import os
from openai import OpenAI

SAMPLE_RATE = 16000
DURATION = 5
AUDIO_FILE = "command.wav"

def record_command():
    print("🎤 Listening for command...")
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    sf.write(AUDIO_FILE, audio, SAMPLE_RATE)
    print("✅ Audio captured:", AUDIO_FILE)

def transcribe_with_whisper():
    client = OpenAI()
    with open(AUDIO_FILE, "rb") as f:
        transcript = client.audio.transcriptions.create(
            file=f,
            model="whisper-1"
        )
    return transcript.text

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable is not set.")
        exit(1)

    record_command()
    text = transcribe_with_whisper()

    print("\n🧠 TRANSCRIBED COMMAND:")
    print(text)

if __name__ == "__main__":
    main()

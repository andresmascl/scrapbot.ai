import asyncio
import json
import os
import io
import wave
import numpy as np
import torch
from google import genai
from google.genai import types

from config import (
    PROJECT_ID,
    MODEL_NAME,
    SILENCE_SECONDS,
    VAD_THRESHOLD,
)
from app_state import listen_state

# -----------------------
# Model / API config
# -----------------------

LOCATION = os.getenv("GCP_REGION", "us-central1")
MODEL_ID = os.getenv("VERTEX_MODEL_NAME", MODEL_NAME)
SILENCE_THRESHOLD_MS = int(float(SILENCE_SECONDS) * 1000)

# ⏱️ Max time to wait for speech AFTER wake word
COMMAND_START_TIMEOUT_SEC = 3.0

print("Loading Silero VAD in reasoner...", flush=True)
vad_model, _ = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    force_reload=False,
    trust_repo=True,
)


def get_system_instruction():
    try:
        with open("PROMPT.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a helpful assistant."


async def transcribe_audio(client, audio_bytes: bytes) -> str:
    print("✍️ Transcribing...", flush=True)

    try:
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_bytes)

            response = await client.aio.models.generate_content(
                model=MODEL_ID,
                contents=[
                    types.Part(text="Transcribe the audio exactly."),
                    types.Part(
                        inline_data=types.Blob(
                            data=wav_buffer.getvalue(),
                            mime_type="audio/wav",
                        )
                    ),
                ],
            )

        return response.text.strip()

    except Exception as e:
        print(f"⚠️ STT error: {e}", flush=True)
        return ""


async def process_voice_command(audio_gen):
    """
    Consume audio AFTER wake word.
    Start recording on first detected speech.
    Stop after sustained silence.
    Cancel if no speech starts within timeout.
    """

    # -----------------------
    # Client setup
    # -----------------------
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        client = genai.Client(
            project=PROJECT_ID,
            location=LOCATION,
        )

    system_instruction = get_system_instruction()

    frames: list[bytes] = []
    vad_buffer = b""

    speaking = False
    silence_start = None

    # ⏱️ Start timeout clock
    loop = asyncio.get_running_loop()
    start_time = loop.time()

    print("👂 Listening for command (reasoner)...", flush=True)

    async for chunk in audio_gen:
        if isinstance(chunk, str):
            continue

        # ⛔ Timeout: no speech detected
        if not speaking:
            elapsed = loop.time() - start_time
            if elapsed > COMMAND_START_TIMEOUT_SEC:
                print(
                    f"⏱️ No speech detected after "
                    f"{COMMAND_START_TIMEOUT_SEC:.1f}s — cancelling",
                    flush=True,
                )
                return None

        vad_buffer += chunk

        while len(vad_buffer) >= 1024:
            block = vad_buffer[:1024]
            vad_buffer = vad_buffer[1024:]

            audio = (
                np.frombuffer(block, dtype=np.int16)
                .astype(np.float32)
                / 32768.0
            )

            try:
                prob = vad_model(torch.from_numpy(audio), 16000).item()
            except Exception:
                prob = 0.0

            if prob > float(VAD_THRESHOLD):
                if not speaking:
                    print("🗣️ Speech started", flush=True)
                speaking = True
                silence_start = None
                frames.append(block)

            elif speaking:
                if silence_start is None:
                    silence_start = loop.time()

                elapsed = (loop.time() - silence_start) * 1000
                frames.append(block)

                if elapsed > SILENCE_THRESHOLD_MS:
                    print("\n🛑 Silence detected. Processing...", flush=True)
                    break
        else:
            continue

        break  # silence detected

    if not frames:
        print("⚠️ No speech captured.", flush=True)
        return None

    audio_bytes = b"".join(frames)

    transcript = await transcribe_audio(client, audio_bytes)
    if not transcript:
        return None

    print(f"\n🗣️ Transcript: {transcript}", flush=True)
    print(f"🤔 Thinking with {MODEL_ID}...", flush=True)

    try:
        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=transcript,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            ),
        )

        raw = response.text or ""
        print("\n🤖 Raw LLM Response:\n", raw, flush=True)

        clean = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)

        print("\n✅ Parsed JSON:")
        print(json.dumps(data, indent=2), flush=True)

    except Exception as e:
        print(f"❌ LLM error: {e}", flush=True)
        return None

    return data

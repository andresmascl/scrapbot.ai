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


async def process_voice_command(audio_gen):
    """
    Consume audio AFTER wake word.
    Start recording on first detected speech.
    Stop after sustained silence.
    Cancel if no speech starts within timeout.

    SINGLE CALL:
    Audio -> transcript + intent JSON
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

    print("🤔 Transcribing + inferring intent...", flush=True)

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
                    types.Part(
                        text=(
                            "You are a voice assistant.\n"
                            "The user speaks either English or Spanish.\n\n"
                            "Tasks:\n"
                            "1) Transcribe the audio exactly.\n"
                            "2) Infer the user's intent.\n\n"
                            "Return STRICT JSON with this shape:\n"
                            "{\n"
                            "  \"transcript\": string,\n"
                            "  \"intent\": string,\n"
                            "  \"filter\": string | null,\n"
                            "  \"feedback\": string | null,\n"
                            "  \"confidence\": number\n"
                            "}\n"
                        )
                    ),
                    types.Part(
                        inline_data=types.Blob(
                            data=wav_buffer.getvalue(),
                            mime_type="audio/wav",
                        )
                    ),
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                ),
            )

        raw = response.text or ""
        clean = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)

        transcript = data.get("transcript")
        if transcript:
            print(f"\n🗣️ Transcript: {transcript}", flush=True)

        print("\n✅ Parsed JSON:")
        print(json.dumps(data, indent=2), flush=True)

        return data

    except Exception as e:
        print(f"❌ LLM error: {e}", flush=True)
        return None

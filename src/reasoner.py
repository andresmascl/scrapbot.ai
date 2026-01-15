import asyncio
import json
import logging
import os
import io
import wave
import numpy as np
import torch
from google import genai
from google.genai import types

from src.config import (
    COMMAND_TIMEOUT,
    PROJECT_ID,
    MODEL_NAME,
    SILENCE_SECONDS,
    VAD_THRESHOLD,
)
from src.app_state import listen_state

# -----------------------
# Model / API config
# -----------------------

LOCATION = os.getenv("GCP_REGION", "us-central1")
MODEL_ID = os.getenv("VERTEX_MODEL_NAME", MODEL_NAME)
SILENCE_THRESHOLD_MS = int(float(SILENCE_SECONDS) * 1000)

logging.debug("Loading Silero VAD in reasoner...")
vad_model, _ = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    force_reload=False,
    trust_repo=True,
)

# -----------------------
# AEC-safe VAD parameters
# -----------------------

NOISE_ALPHA = 0.95          # slow adaptation
SILENCE_RELATIVE_K = 1.4    # silence = near noise floor


def get_system_instruction():
    try:
        # Get path relative to project root (main.py's location)
        prompt_path = os.path.join(os.getcwd(), "docs", "PROMPT.md")
        with open(prompt_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a helpful assistant."


async def process_voice_command(audio_gen):
    """
    Consume audio AFTER wake word.
    Start recording on first detected speech.
    Stop after sustained *relative* silence (AEC-safe).
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

    # 🔊 Adaptive noise floor (VAD probability)
    noise_floor = None

    # ⏱️ Start timeout clock
    loop = asyncio.get_running_loop()
    start_time = loop.time()

    logging.info("👂 Listening for command (reasoner)...")

    async for chunk in audio_gen:
        if isinstance(chunk, str):
            continue

        # ⛔ Timeout: no speech detected
        if not speaking:
            elapsed = loop.time() - start_time
            if elapsed > COMMAND_TIMEOUT:
                logging.warning(
                    f"⏱️ No speech detected after "
                    f"{COMMAND_TIMEOUT:.1f}s — cancelling"
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

            # -----------------------
            # Initialize noise floor
            # -----------------------
            if noise_floor is None:
                noise_floor = prob

            # -----------------------
            # Speech detection
            # -----------------------
            if prob > max(float(VAD_THRESHOLD), noise_floor * 2.0):
                if not speaking:
                    logging.info("🗣️ Speech started")
                speaking = True
                silence_start = None
                frames.append(block)
                continue

            # -----------------------
            # Update noise floor ONLY when not speaking
            # -----------------------
            if not speaking:
                noise_floor = (
                    NOISE_ALPHA * noise_floor
                    + (1 - NOISE_ALPHA) * prob
                )
                continue

            # -----------------------
            # Relative silence detection (AEC-safe)
            # -----------------------
            frames.append(block)

            if prob < noise_floor * SILENCE_RELATIVE_K:
                if silence_start is None:
                    silence_start = loop.time()

                elapsed = (loop.time() - silence_start) * 1000

                if elapsed > SILENCE_THRESHOLD_MS:
                    logging.info("🛑 Silence detected. Processing...")
                    break
            else:
                silence_start = None

        else:
            continue

        break  # silence detected

    if not frames:
        logging.warning("⚠️ No speech captured.")
        return None

    audio_bytes = b"".join(frames)

    logging.info("🤔 Transcribing + inferring intent...")

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
                            "  \"language\": \"en\" | \"es\",\n"
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
            logging.info(f"🗣️ Transcript: {transcript}")

        logging.debug("✅ Parsed JSON:")
        logging.debug(json.dumps(data, indent=2))

        return data

    except Exception as e:
        logging.error(f"❌ LLM error: {e}")
        return None

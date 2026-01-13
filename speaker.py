import asyncio
import logging
import os
from typing import Optional

from app_state import listen_state

# -----------------------
# Speaker configuration
# -----------------------

# Piper TTS Configuration
PIPER_DIR = "piper_tts"
PIPER_BIN = os.path.join(PIPER_DIR, "piper")

# Voice Models
VOICE_EN = os.path.join(PIPER_DIR, "en_US-lessac-medium.onnx")
VOICE_ES = os.path.join(PIPER_DIR, "es_ES-sharvard-medium.onnx")

# Playback
APLAY_BIN = "aplay"
SAMPLE_RATE = 22050  # Piper medium voices are typically 22050 Hz
CHANNELS = 1
FORMAT = "S16_LE"


# -----------------------
# Internal helpers
# -----------------------

async def _tts_to_wav(text: str, language: str = "en") -> bytes:
    """
    Convert text to raw PCM audio bytes using Piper TTS.
    """
    model = VOICE_ES if language == "es" else VOICE_EN

    if not os.path.exists(PIPER_BIN):
        logging.error(f"❌ Piper binary not found at {PIPER_BIN}")
        return b""

    if not os.path.exists(model):
        logging.error(f"❌ Voice model not found: {model}")
        return b""

    try:
        proc = await asyncio.create_subprocess_exec(
            PIPER_BIN,
            "--model", model,
            "--output_raw",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )

        stdout, _ = await proc.communicate(input=text.encode("utf-8"))
        return stdout
        
    except Exception as e:
        logging.error(f"❌ Piper TTS execution failed: {e}")
        return b""


async def _play_wav(audio: bytes):
    """
    Play raw PCM bytes via aplay (clean ALSA / PipeWire lifecycle).
    """
    if not audio:
        return

    try:
        proc = await asyncio.create_subprocess_exec(
            APLAY_BIN,
            "-q",
            "-f", FORMAT,
            "-c", str(CHANNELS),
            "-r", str(SAMPLE_RATE),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

        proc.stdin.write(audio)
        await proc.stdin.drain()
        proc.stdin.close()
        await proc.wait()

    except Exception as e:
        logging.error(f"❌ Audio playback failed: {e}")


# -----------------------
# Public API (used by main.py)
# -----------------------

async def speak(text: Optional[str], language: str = "en"):
    """
    Speak text safely:
    - pauses listener
    - blocks wake word
    - guarantees cleanup
    """
    if not text:
        return

    await listen_state.block_listener()
    await listen_state.block_global_wake_word()

    try:
        # Generate audio
        audio = await _tts_to_wav(text, language)
        
        # Play audio
        if audio:
            await _play_wav(audio)

    except Exception as e:
        logging.warning(f"⚠️ Speaker error (ignored): {e}")

    finally:
        await listen_state.allow_listener()
        await listen_state.allow_global_wake_word()

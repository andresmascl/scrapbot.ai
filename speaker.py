import asyncio
import subprocess
from typing import Optional

from app_state import listen_state

# -----------------------
# Speaker configuration
# -----------------------

ESPEAK_BIN = "espeak-ng"

# We generate WAV and play it synchronously so:
# - no orphan ffplay processes
# - PipeWire apps close cleanly
APLAY_BIN = "aplay"

SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = "S16_LE"


# -----------------------
# Internal helpers
# -----------------------

async def _tts_to_wav(text: str) -> bytes:
    """
    Convert text to WAV audio bytes using espeak-ng.
    """
    proc = await asyncio.create_subprocess_exec(
        ESPEAK_BIN,
        "--stdout",
        "-s", "170",
        "-v", "en",
        text,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    audio = await proc.stdout.read()
    await proc.wait()
    return audio


async def _play_wav(audio: bytes):
    """
    Play WAV bytes via aplay (clean ALSA / PipeWire lifecycle).
    """
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


# -----------------------
# Public API (used by main.py)
# -----------------------

async def speak(text: Optional[str]):
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
        audio = await _tts_to_wav(text)
        if audio:
            await _play_wav(audio)

    except Exception as e:
        print(f"⚠️ Speaker error (ignored): {e}", flush=True)

    finally:
        await listen_state.allow_listener()
        await listen_state.allow_global_wake_word()

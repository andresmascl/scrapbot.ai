import asyncio
import numpy as np
import audioop
import subprocess
import math
import threading
from openwakeword.model import Model

from config import WAKE_KEY, WAKE_THRESHOLD, FRAME_SIZE
from app_state import listen_state

import os

# =========================
# Constants
# =========================

READ_CHUNK_SIZE = FRAME_SIZE
WAKE_SOUND_PATH = "/app/wakeword-confirmed.mp3"

# 1 second @ 16kHz, int16
WAKE_WINDOW_SAMPLES = 16000
WAKE_WINDOW_BYTES = WAKE_WINDOW_SAMPLES * 2

ENABLE_VOLUME_BAR = os.getenv("ENABLE_VOLUME_BAR", "0") == "1"

print("Loading Wake Word model...", flush=True)

try:
    wake_model = Model(wakeword_models=[WAKE_KEY])
except TypeError:
    print(
        f"⚠️ Argument mismatch. Loading default models and filtering for {WAKE_KEY}...",
        flush=True,
    )
    wake_model = Model()

wake_model_lock = threading.Lock()


async def play_wake_sound():
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-loglevel",
            "quiet",
            WAKE_SOUND_PATH,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await proc.wait()
    except Exception:
        pass


async def listen(stream, native_rate):
    """
    Long-lived async generator.
    Mic → resample → buffer → wake-word detection → yield audio / START_SESSION
    """

    print(
        f"\n🎙️ Listener running — resampling {native_rate}Hz → 16kHz\n",
        flush=True,
    )

    resample_state = None

    try:
        while await listen_state.get_listener_running():
            # -------------------------
            # Read from microphone
            # -------------------------
            data = await asyncio.to_thread(
                stream.read,
                READ_CHUNK_SIZE,
                exception_on_overflow=False,
            )

            # -------------------------
            # Resample to 16kHz mono
            # -------------------------
            resampled, resample_state = audioop.ratecv(
                data,
                2,      # width (int16)
                1,      # channels
                native_rate,
                16000,
                resample_state,
            )

            # -------------------------
            # Optional volume bar
            # -------------------------
            if ENABLE_VOLUME_BAR:
                try:
                    rms = audioop.rms(resampled, 2)
                    db = 20 * math.log10(max(1, rms))
                    filled = int(min(db, 80) / 80 * 50)
                    bar = "█" * filled
                    print(
                        f"\033[F\033[K🔊 Volume: {rms:5d} |{bar}",
                        flush=True,
                    )
                except Exception:
                    pass

            # -------------------------
            # Wake-word detection
            # -------------------------
            if await listen_state.get_global_wake_word():
                audio_buffer = await listen_state.add_to_audio_buffer(resampled)

                if len(audio_buffer) >= WAKE_WINDOW_BYTES:
                    frame = audio_buffer[-WAKE_WINDOW_BYTES:]
                    audio_frame = np.frombuffer(frame, dtype=np.int16)

                    def _predict():
                        with wake_model_lock:
                            return wake_model.predict(audio_frame)

                    predictions = await asyncio.to_thread(_predict)
                    score = predictions.get(WAKE_KEY, 0.0)

                    if score > WAKE_THRESHOLD:
                        allowed = await listen_state.allow_global_wake_word()
                        print(
                            f"🔔 Wake word score: {score:.3f} "
                            f"(threshold: {WAKE_THRESHOLD}, allowed: {allowed})",
                            flush=True,
                        )

                        await play_wake_sound()

                        await listen_state.empty_audio_buffer()

                        with wake_model_lock:
                            wake_model.reset()

                        yield "START_SESSION"
                        continue

            # -------------------------
            # Normal audio passthrough
            # -------------------------
            yield resampled

    finally:
        print("🛑 Listener stopped.", flush=True)

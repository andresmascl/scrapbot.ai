import asyncio
import numpy as np
import audioop
import subprocess
import threading
import os
import time

from openwakeword.model import Model
from config import WAKE_KEY, WAKE_THRESHOLD, FRAME_SIZE
from app_state import listen_state

# -------------------------
# Constants
# -------------------------

READ_CHUNK_SIZE = FRAME_SIZE
WAKE_SOUND_PATH = "/app/wakeword-confirmed.mp3"

SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2  # int16

WAKE_WINDOW_SEC = 1.0
WAKE_WINDOW_BYTES = int(SAMPLE_RATE * SAMPLE_WIDTH * WAKE_WINDOW_SEC)

PREDICT_EVERY_SEC = 0.2  # 200 ms

ENABLE_VOLUME_BAR = os.getenv("ENABLE_VOLUME_BAR", "0") == "1"

# -------------------------
# Wake-word model
# -------------------------

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

# -------------------------
# Helpers
# -------------------------

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


# -------------------------
# Listener
# -------------------------

async def listen(stream, native_rate):
    print(
        f"\n🎙️ Listener running — input={native_rate}Hz → 16kHz | "
        f"FRAME_SIZE={FRAME_SIZE} | "
        f"WAKE_WINDOW_BYTES={WAKE_WINDOW_BYTES}\n",
        flush=True,
    )

    resample_state = None
    wake_buffer = bytearray()
    last_predict_time = 0.0

    while await listen_state.get_listener_running():
        # -------------------------
        # Always read audio
        # -------------------------
        data = await asyncio.to_thread(
            stream.read,
            READ_CHUNK_SIZE,
            exception_on_overflow=False,
        )

        # -------------------------
        # Resample to 16 kHz
        # -------------------------
        resampled, resample_state = audioop.ratecv(
            data,
            SAMPLE_WIDTH,
            1,
            native_rate,
            SAMPLE_RATE,
            resample_state,
        )

        # ✅ ALWAYS yield audio
        yield resampled

        # -------------------------
        # Volume diagnostics
        # -------------------------
        if ENABLE_VOLUME_BAR:
            rms = audioop.rms(resampled, SAMPLE_WIDTH)
            filled = int(min(rms, 2000) / 2000 * 30)

            print(
                f"\033[F\033[K"
                f"🔊 RMS:{rms:5d} |{'█' * filled:<30} "
                f"BUF:{len(wake_buffer):6d}/{WAKE_WINDOW_BYTES}",
                flush=True,
            )

        # -------------------------
        # Wake-word detection ONLY if allowed
        # -------------------------
        if not await listen_state.get_global_wake_word():
            continue

        # -------------------------
        # Overwrite-only buffer
        # -------------------------
        wake_buffer.extend(resampled)
        if len(wake_buffer) > WAKE_WINDOW_BYTES:
            wake_buffer[:] = wake_buffer[-WAKE_WINDOW_BYTES:]

        # -------------------------
        # Cadenced prediction
        # -------------------------
        now = time.monotonic()

        if (
            len(wake_buffer) == WAKE_WINDOW_BYTES
            and now - last_predict_time >= PREDICT_EVERY_SEC
        ):
            last_predict_time = now

            frame = np.frombuffer(bytes(wake_buffer), dtype=np.int16)

            def _predict():
                with wake_model_lock:
                    return wake_model.predict(frame)

            scores = await asyncio.to_thread(_predict)
            score = scores.get(WAKE_KEY, 0.0)

            if score >= WAKE_THRESHOLD:
                print(
                    f"\n🔔 Wake word detected "
                    f"(score={score:.3f}, window={WAKE_WINDOW_SEC:.1f}s)",
                    flush=True,
                )

                await play_wake_sound()

                wake_buffer.clear()
                wake_model.reset()
                last_predict_time = 0.0

                yield "START_SESSION"

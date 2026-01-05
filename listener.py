import asyncio
import numpy as np
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

WAKE_SOUND_PATH = os.path.join(
    os.path.dirname(__file__),
    "wakeword-confirmed.mp3",
)

SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2  # int16

WAKE_WINDOW_SEC = 1.0
WAKE_WINDOW_BYTES = int(SAMPLE_RATE * SAMPLE_WIDTH * WAKE_WINDOW_SEC)

PREDICT_EVERY_SEC = 0.2  # 200 ms
WAKE_COOLDOWN_SEC = 0.6  # feedback suppression

ENABLE_VOLUME_BAR = os.getenv("ENABLE_VOLUME_BAR", "0") == "1"

# -------------------------
# Helpers
# -------------------------

def rms_int16(frame: bytes) -> int:
    samples = np.frombuffer(frame, dtype=np.int16)
    if samples.size == 0:
        return 0
    return int(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))


def resample_int16(data: bytes, src_rate: int, dst_rate: int) -> bytes:
    if src_rate == dst_rate:
        return data

    samples = np.frombuffer(data, dtype=np.int16)
    if samples.size == 0:
        return data

    duration = samples.size / src_rate
    target_len = int(duration * dst_rate)

    resampled = np.interp(
        np.linspace(0.0, samples.size, target_len, endpoint=False),
        np.arange(samples.size),
        samples,
    ).astype(np.int16)

    return resampled.tobytes()


def play_wake_sound():
    if not os.path.exists(WAKE_SOUND_PATH):
        print(f"⚠️ Wake sound not found: {WAKE_SOUND_PATH}", flush=True)
        return

    try:
        subprocess.Popen(
            ["paplay", WAKE_SOUND_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"⚠️ Failed to play wake sound: {e}", flush=True)


async def wake_cooldown():
    await asyncio.sleep(WAKE_COOLDOWN_SEC)

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
# Listener
# -------------------------

async def listen(stream, native_rate):
    print(
        f"\n🎙️ Listener running — input={native_rate}Hz → 16kHz | "
        f"FRAME_SIZE={FRAME_SIZE} | "
        f"WAKE_WINDOW_BYTES={WAKE_WINDOW_BYTES}\n",
        flush=True,
    )

    wake_buffer = bytearray()
    last_predict_time = 0.0

    # 🔒 LOCAL cooldown flag (THIS WAS MISSING)
    in_wake_cooldown = False

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
        resampled = resample_int16(
            data=data,
            src_rate=native_rate,
            dst_rate=SAMPLE_RATE,
        )

        # ✅ ALWAYS yield audio
        yield resampled

        # -------------------------
        # Volume diagnostics
        # -------------------------
        if ENABLE_VOLUME_BAR:
            rms = rms_int16(resampled)
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

            if score >= WAKE_THRESHOLD and not in_wake_cooldown:
                print(
                    f"\n🔔 Wake word detected "
                    f"(score={score:.3f}, window={WAKE_WINDOW_SEC:.1f}s)",
                    flush=True,
                )

                in_wake_cooldown = True

                # 🔔 Play wake sound
                play_wake_sound()

                # 🧹 Reset buffers so sound cannot retrigger
                wake_buffer.clear()
                wake_model.reset()
                last_predict_time = 0.0

                # 🚀 Signal main loop
                yield "START_SESSION"

                # ⏳ Cooldown to absorb speaker bleed
                await wake_cooldown()
                in_wake_cooldown = False

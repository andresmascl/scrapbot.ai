import asyncio
import numpy as np
import audioop
import subprocess
import math
import threading
import os

from openwakeword.model import Model
from config import WAKE_KEY, WAKE_THRESHOLD, FRAME_SIZE
from app_state import listen_state

READ_CHUNK_SIZE = FRAME_SIZE
WAKE_SOUND_PATH = "/app/wakeword-confirmed.mp3"

WAKE_WINDOW_SAMPLES = 16000
WAKE_WINDOW_BYTES = WAKE_WINDOW_SAMPLES * 2

ENABLE_VOLUME_BAR = os.getenv("ENABLE_VOLUME_BAR", "0") == "1"

print("Loading Wake Word model...", flush=True)

try:
    wake_model = Model(wakeword_models=[WAKE_KEY])
except TypeError:
    print(f"⚠️ Argument mismatch. Loading default models and filtering for {WAKE_KEY}...")
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
    print(f"\n🎙️ Listener running — resampling {native_rate}Hz → 16kHz\n", flush=True)

    resample_state = None
    wake_buffer = b""

    while await listen_state.get_listener_running():
        data = await asyncio.to_thread(
            stream.read,
            READ_CHUNK_SIZE,
            exception_on_overflow=False,
        )

        resampled, resample_state = audioop.ratecv(
            data, 2, 1, native_rate, 16000, resample_state
        )

        # -------------------------
        # Volume + buffer display
        # -------------------------
        if ENABLE_VOLUME_BAR:
            rms = audioop.rms(resampled, 2)
            filled = int(min(rms, 2000) / 2000 * 40)
            buffer_size = len(wake_buffer)

            print(
                f"\033[F\033[K"
                f"🔊 Volume: {rms:5d} |{'█' * filled:<40} "
                f"📦 Buffer: {buffer_size:6d} bytes",
                flush=True,
            )

        # -------------------------
        # Passthrough if wake blocked
        # -------------------------
        if not await listen_state.get_global_wake_word():
            yield resampled
            continue

        # -------------------------
        # Wake-word rolling buffer
        # -------------------------
        wake_buffer += resampled
        if len(wake_buffer) > WAKE_WINDOW_BYTES:
            wake_buffer = wake_buffer[-WAKE_WINDOW_BYTES:]

        # -------------------------
        # Wake-word detection
        # -------------------------
        if len(wake_buffer) == WAKE_WINDOW_BYTES:
            frame = np.frombuffer(wake_buffer, dtype=np.int16)

            def _predict():
                with wake_model_lock:
                    return wake_model.predict(frame)

            score = (await asyncio.to_thread(_predict)).get(WAKE_KEY, 0.0)

            if score > WAKE_THRESHOLD:
                print(f"🔔 Wake word detected (score={score:.3f})", flush=True)
                await play_wake_sound()
                wake_buffer = b""
                wake_model.reset()
                yield "START_SESSION"
                continue

        yield resampled

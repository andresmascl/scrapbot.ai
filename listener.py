import asyncio
import numpy as np
import audioop
import time
import subprocess
import math
import sys
import threading
from openwakeword.model import Model
from config import WAKE_KEY, WAKE_THRESHOLD, WAKE_COOLDOWN_SEC, FRAME_SIZE
import os

# Constants
READ_CHUNK_SIZE = FRAME_SIZE
WAKE_SOUND_PATH = "/app/wakeword-confirmed.mp3"

ENABLE_VOLUME_BAR = os.getenv("ENABLE_VOLUME_BAR", "0") == "1"

print("Loading Wake Word model...", flush=True)

try:
    wake_model = Model(wakeword_models=[WAKE_KEY])
except TypeError:
    print(f"⚠️ Argument mismatch. Loading default models and filtering for {WAKE_KEY}...", flush=True)
    wake_model = Model()

wake_model_lock = threading.Lock()

# ======================
# Listener global state
# ======================
global_wake_allowed = True
_listener_running = True
_rearm_task = None
_wake_worker_task = None


def stop():
    """
    Gracefully stop the listener and its background tasks.
    Safe to call multiple times.
    """
    global _listener_running, global_wake_allowed, _rearm_task, _wake_worker_task

    _listener_running = False
    global_wake_allowed = False

    # cancel delayed re-arm
    try:
        if isinstance(_rearm_task, asyncio.Task) and not _rearm_task.done():
            _rearm_task.cancel()
    except Exception:
        pass

    # cancel wake worker
    try:
        if isinstance(_wake_worker_task, asyncio.Task) and not _wake_worker_task.done():
            _wake_worker_task.cancel()
    except Exception:
        pass


def rearm_wake_word(delay: float = 0.0, clear_queue: bool = False):
    """
    Re-enable wake detection.

    If delay > 0, keep the gate CLOSED for `delay` seconds to avoid
    retriggering from TTS or echo.

    If clear_queue is True, clears the audio queue to prevent processing
    old audio that might contain TTS feedback.
    """
    global global_wake_allowed, _rearm_task

    # cancel any pending delayed rearm
    try:
        if isinstance(_rearm_task, asyncio.Task) and not _rearm_task.done():
            _rearm_task.cancel()
    except Exception:
        pass

    if delay <= 0:
        global_wake_allowed = True
        return

    global_wake_allowed = False

    # Clear both audio and event queues to prevent processing old TTS feedback
    # and any pending START_SESSION events from false detections
    if clear_queue:
        try:
            loop = asyncio.get_running_loop()
            # Clear audio queue
            if hasattr(rearm_wake_word, '_audio_queue'):
                while not rearm_wake_word._audio_queue.empty():
                    try:
                        rearm_wake_word._audio_queue.get_nowait()
                    except:
                        break
            # Clear event queue to remove any pending START_SESSION events
            if hasattr(rearm_wake_word, '_event_queue'):
                while not rearm_wake_word._event_queue.empty():
                    try:
                        rearm_wake_word._event_queue.get_nowait()
                    except:
                        break
        except Exception:
            pass

    async def _delayed_rearm():
        try:
            await asyncio.sleep(delay)
            global global_wake_allowed
            global_wake_allowed = True
        except asyncio.CancelledError:
            return

    try:
        loop = asyncio.get_running_loop()
        _rearm_task = loop.create_task(_delayed_rearm())
    except RuntimeError:
        def _sync_rearm():
            global global_wake_allowed
            global_wake_allowed = True

        t = threading.Timer(delay, _sync_rearm)
        t.daemon = True
        t.start()
        _rearm_task = t


async def play_wake_sound():
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
            WAKE_SOUND_PATH,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        await proc.wait()
    except Exception:
        pass


async def listen(stream, native_rate):
    """
    Long-lived async generator.
    Runs until listener.stop() is called.
    """
    global _wake_worker_task

    audio_queue = asyncio.Queue(maxsize=100)
    event_queue = asyncio.Queue()

    # Store queue references so rearm_wake_word can clear them
    rearm_wake_word._audio_queue = audio_queue
    rearm_wake_word._event_queue = event_queue

    async def wake_word_worker():
        global global_wake_allowed

        with wake_model_lock:
            wake_model.reset()

        audio_buffer = b""
        local_cooldown_until = 0.0

        try:
            while _listener_running:
                if not global_wake_allowed:
                    await asyncio.sleep(0.05)
                    continue

                chunk = await audio_queue.get()
                audio_buffer += chunk

                if len(audio_buffer) > 32000:
                    audio_buffer = audio_buffer[-32000:]

                while len(audio_buffer) >= 2560:
                    frame = audio_buffer[:2560]
                    audio_buffer = audio_buffer[2560:]

                    audio_frame = np.frombuffer(frame, dtype=np.int16)
                    now = time.time()

                    if now < local_cooldown_until:
                        continue

                    def _predict():
                        with wake_model_lock:
                            return wake_model.predict(audio_frame)

                    predictions = await asyncio.to_thread(_predict)
                    score = predictions.get(WAKE_KEY, 0.0)

                    if score > WAKE_THRESHOLD:
                        asyncio.create_task(play_wake_sound())

                        local_cooldown_until = now + WAKE_COOLDOWN_SEC

                        # Check if wake is still allowed before adding event
                        # This prevents race condition where we process old audio
                        # after global_wake_allowed was set to False
                        if not global_wake_allowed:
                            continue

                        global_wake_allowed = False

                        while not audio_queue.empty():
                            try:
                                audio_queue.get_nowait()
                            except asyncio.QueueEmpty:
                                break

                        await event_queue.put("START_SESSION")
        except asyncio.CancelledError:
            pass

    _wake_worker_task = asyncio.create_task(wake_word_worker())

    print(f"🎙️ Listener running — resampling {native_rate}Hz → 16kHz", flush=True)
    resample_state = None

    try:
        while _listener_running:
            data = await asyncio.to_thread(
                stream.read,
                READ_CHUNK_SIZE,
                exception_on_overflow=False,
            )

            resampled, resample_state = audioop.ratecv(
                data, 2, 1, native_rate, 16000, resample_state
            )

            if ENABLE_VOLUME_BAR:
                try:
                    rms = audioop.rms(resampled, 2)
                    db = 20 * math.log10(max(1, rms))
                    filled = int(min(db, 80) / 80 * 50)
                    bar = "█" * filled
                    print(f"\033[F\033[K🔊 Volume: {rms:5d} |{bar}", flush=True)
                except Exception:
                    pass

            try:
                event = event_queue.get_nowait()
                if event == "START_SESSION":
                    yield "START_SESSION"
            except asyncio.QueueEmpty:
                pass

            yield resampled

            if global_wake_allowed and not audio_queue.full():
                audio_queue.put_nowait(resampled)

    finally:
        stop()
        print("🛑 Listener stopped.", flush=True)

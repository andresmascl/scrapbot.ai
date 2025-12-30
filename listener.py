import asyncio
import numpy as np
import audioop
import subprocess
import math
import threading
from openwakeword.model import Model
from config import WAKE_KEY, WAKE_THRESHOLD, FRAME_SIZE
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
_rearm_generation = 0  # Incremented each time rearm_wake_word is called


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


def rearm_wake_word():
	"""
	Re-enable wake detection.
	"""
	global global_wake_allowed, _rearm_task, _rearm_generation

	# Increment generation to invalidate old pending rearm tasks
	_rearm_generation += 1
	current_generation = _rearm_generation
	print(f"🔄 Rearm generation: {current_generation}", flush=True)
	print(f"🔀 Setting global_wake_allowed = False rearm_wake_word", flush=True)
	global_wake_allowed = False



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

	async def wake_word_worker():
		global global_wake_allowed

		with wake_model_lock:
			wake_model.reset()

		audio_buffer = b""

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

					def _predict():
						with wake_model_lock:
							return wake_model.predict(audio_frame)

					predictions = await asyncio.to_thread(_predict)
					score = predictions.get(WAKE_KEY, 0.0)

					if score > WAKE_THRESHOLD:
						global_wake_allowed = False
						print(f"🔔 Wake word score: {score:.3f} (threshold: {WAKE_THRESHOLD}, allowed: {global_wake_allowed})", flush=True)
						
						asyncio.create_task(play_wake_sound())
						audio_buffer = b""	# reset buffer after detection
						print(f"✅ Adding START_SESSION to event_queue", flush=True)
						print(f"🔀 Setting global_wake_allowed = False (wake word detected)\n", flush=True)
						await event_queue.put("START_SESSION")

		except asyncio.CancelledError:
			pass

	_wake_worker_task = asyncio.create_task(wake_word_worker())

	print(f"\n🎙️ Listener running — resampling {native_rate}Hz → 16kHz\n", flush=True)
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

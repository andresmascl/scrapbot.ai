import asyncio
import numpy as np
import audioop
import time
import torch
import subprocess
import math
import sys
from openwakeword.model import Model
from config import (
	WAKE_KEY, WAKE_THRESHOLD, WAKE_COOLDOWN_SEC, FRAME_SIZE
)

# Constants
READ_CHUNK_SIZE = FRAME_SIZE 
WAKE_SOUND_PATH = "/app/wakeword-confirmed.mp3"

print("Loading Silero VAD and Wake Word models...", flush=True)

try:
	wake_model = Model(wakeword_models=[WAKE_KEY])
except TypeError:
	print(f"⚠️ Argument mismatch. Loading default models and filtering for {WAKE_KEY}...")
	wake_model = Model()

vad_model, _ = torch.hub.load(
	repo_or_dir='snakers4/silero-vad', 
	model='silero_vad', 
	force_reload=False, 
	trust_repo=True
	)

def play_wake_sound():
	try:
		subprocess.Popen(
			["ffplay", "-nodisp", "-autoexit", WAKE_SOUND_PATH], 
			stdout=subprocess.DEVNULL, 
			stderr=subprocess.STDOUT
		)
	except Exception as e:
		print(f"🔊 Playback error: {e}")

async def listen(stream, native_rate):
	audio_queue = asyncio.Queue()
	event_queue = asyncio.Queue()

	async def wake_word_worker():
		audio_buffer = b""
		wake_cooldown_until = 0
		while True:
			chunk = await audio_queue.get()
			audio_buffer += chunk
			
			if len(audio_buffer) > 32000:
				audio_buffer = b""
				continue

			if len(audio_buffer) >= 2560:
				to_process = audio_buffer[:2560]
				audio_buffer = audio_buffer[2560:]
				
				audio_frame = np.frombuffer(to_process, dtype=np.int16)
				
				now = time.time()
				if now > wake_cooldown_until:
					predictions = await asyncio.to_thread(wake_model.predict, audio_frame)
					score = predictions.get(WAKE_KEY, 0)
					if score > WAKE_THRESHOLD:
						print(f"✨ Wake word detected! ({score:.2f})", flush=True)
						play_wake_sound()
						wake_cooldown_until = now + WAKE_COOLDOWN_SEC
						await event_queue.put("START_SESSION")
						
						# Clear audio queue to prevent processing backlog or echoes
						while not audio_queue.empty():
							try: audio_queue.get_nowait()
							except asyncio.QueueEmpty: break

	worker_task = asyncio.create_task(wake_word_worker())

	print(f"🎙️ Listener started. Resampling {native_rate}Hz -> 16000Hz", flush=True)
	resample_state = None

	try:
		while True:
			# Read audio data - the print here forces async cooperation
			data = await asyncio.to_thread(stream.read, READ_CHUNK_SIZE, exception_on_overflow=False)
			
			# Resample to 16kHz
			resampled_chunk, resample_state = audioop.ratecv(
				data, 2, 1, native_rate, 16000, resample_state
			)

			# --- VOLUME BAR VISUALIZATION ---
			# Clear line and print on same line
			rms = audioop.rms(resampled_chunk, 2)
			db = 20 * math.log10(max(1, rms))
			max_db, bar_len = 80, 50
			filled_len = int(min(db, max_db) / max_db * bar_len)
			
			bar = "█" * filled_len + " " * (bar_len - filled_len)
			print(f"\033[F\033[K🔊 Volume: {rms:5d} |{bar}\x1b[K", flush=True)

			# First, check for events
			try:
				event = event_queue.get_nowait()
				if event == "START_SESSION":
					yield "START_SESSION"
			except asyncio.QueueEmpty:
				pass
			
			# Then yield the audio chunk
			yield resampled_chunk
			
			# Add to wake word detection queue
			if audio_queue.qsize() < 50:
				audio_queue.put_nowait(resampled_chunk)

	except Exception as e:
		sys.stdout.write("\x1b[2K\r")  # Clear the line before printing error
		print(f"⚠️ Listener Error: {e}")
	finally:
		worker_task.cancel()
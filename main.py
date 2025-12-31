import asyncio
import pyaudio
import reasoner
import listener
from config import FRAME_SIZE, PROJECT_ID, TTS_REARM_DELAY_SEC
import os
from app_state import listen_state
from ctypes import *
from contextlib import contextmanager

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
def py_error_handler(filename, line, function, err, fmt):
    pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def no_alsa_err():
    try:
        asound = cdll.LoadLibrary('libasound.so.2')
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except Exception:
        yield


async def main_loop():
	main_flag=True
	while main_flag:
		missing = []
		if not PROJECT_ID:
			missing.append("GCP_PROJECT_ID")
		if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not os.getenv("GOOGLE_APPLICATIONS_CREDENTIALS") and not os.getenv("GOOGLE_CREDENTIALS"):
			missing.append("GOOGLE_APPLICATION_CREDENTIALS")
		if missing:
			raise RuntimeError(f"Missing required environment: {', '.join(missing)}")

		with no_alsa_err():
			p = pyaudio.PyAudio()

		device_info = p.get_default_input_device_info()
		native_rate = int(device_info['defaultSampleRate'])

		stream = p.open(
			format=pyaudio.paInt16,
			channels=1,
			rate=native_rate,
			input=True,
			frames_per_buffer=FRAME_SIZE,
		)

		print("🤖 Scrapbot is active. Say the wake word.", flush=True)
		await listen_state.allow_global_wake_word()
		audio_gen = listener.listen(stream, native_rate=native_rate)

		# allow wake word detection
		await listen_state.allow_global_wake_word()

		try:
			async for item in audio_gen:
				if item == "START_SESSION":
					if await listen_state.get_global_wake_word() is False:
						continue
					else:
						listen_state.block_global_wake_word()
					
					listen_state.empty_audio_buffer()


					print("🛰️ Wake word detected! Listening for command...", flush=True)

					result = await reasoner.process_voice_command(audio_gen)
					print(f"📋 Reasoner returned: {result}", flush=True)

					print("🔄 Session complete.", flush=True)
					wake_word_allowed = await listen_state.allow_global_wake_word()
					print(f"listener.global_wake_allowed = {wake_word_allowed}", flush=True)

		finally:
			p.terminate()
			try:
				stream.stop_stream()
				stream.close()
			except Exception:
				pass


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("🛑 Scrapbot stopped by user.", flush=True)

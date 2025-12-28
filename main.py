import asyncio
import pyaudio
import reasoner
import listener
from config import FRAME_SIZE, PROJECT_ID, TTS_REARM_DELAY_SEC
import os
import sys
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

    audio_gen = listener.listen(stream, native_rate=native_rate)
    in_session = False

    try:
        async for item in audio_gen:
            if item == "START_SESSION":
                if in_session:
                    continue

                in_session = True
                print("🛰️ Wake word detected! Listening for command...", flush=True)

                await reasoner.process_voice_command(audio_gen)

                listener.rearm_wake_word(delay=TTS_REARM_DELAY_SEC, clear_queue=True)
                in_session = False
                print("🔄 Session complete. Wake word re-armed.", flush=True)

    finally:
        listener.stop()
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

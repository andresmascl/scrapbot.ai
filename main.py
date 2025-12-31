import asyncio
import pyaudio
import os
from ctypes import *
from contextlib import contextmanager

import listener
import reasoner
from config import FRAME_SIZE, PROJECT_ID
from app_state import listen_state


# -----------------------
# ALSA error suppression
# -----------------------

ERROR_HANDLER_FUNC = CFUNCTYPE(
    None, c_char_p, c_int, c_char_p, c_int, c_char_p
)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def no_alsa_err():
    try:
        asound = cdll.LoadLibrary("libasound.so.2")
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except Exception:
        yield


# -----------------------
# Main loop
# -----------------------

async def main_loop():
    if not PROJECT_ID:
        raise RuntimeError("Missing GCP_PROJECT_ID")

    if not (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or os.getenv("GOOGLE_API_KEY")
    ):
        raise RuntimeError("Missing Google credentials")

    with no_alsa_err():
        p = pyaudio.PyAudio()

    device_info = p.get_default_input_device_info()
    native_rate = int(device_info["defaultSampleRate"])

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

    try:
        async for item in audio_gen:
            if item != "START_SESSION":
                continue

            if not await listen_state.get_global_wake_word():
                continue

            await listen_state.block_global_wake_word()
            print("🛰️ Listening for command...", flush=True)

            result = await reasoner.process_voice_command(audio_gen)
            print(f"📋 Reasoner returned: {result}", flush=True)

            print("🔄 Session complete. Re-arming wake word.", flush=True)
            await listen_state.allow_global_wake_word()

    finally:
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        p.terminate()


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("🛑 Scrapbot stopped by user.", flush=True)

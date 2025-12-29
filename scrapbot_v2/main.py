"""
Simple main entry point for scrapbot_v2.
Sets up PyAudio stream and runs the linear session loop.
"""
import asyncio
import os
import sys
import pyaudio
from ctypes import *
from contextlib import contextmanager

from .config import FRAME_SIZE, PROJECT_ID
from .session import run_session_loop


# ALSA error suppression (from original main.py)
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)


@contextmanager
def no_alsa_err():
    """Context manager to suppress ALSA errors."""
    try:
        asound = cdll.LoadLibrary('libasound.so.2')
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except Exception:
        yield


async def main():
    """
    Main entry point.
    Sets up audio stream and runs session loop.
    """
    # Validate environment variables
    missing = []
    if not PROJECT_ID:
        missing.append("GCP_PROJECT_ID")

    google_creds = (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or
        os.getenv("GOOGLE_APPLICATIONS_CREDENTIALS") or
        os.getenv("GOOGLE_CREDENTIALS") or
        os.getenv("GOOGLE_API_KEY")
    )

    if not google_creds:
        missing.append("GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_API_KEY")

    if missing:
        raise RuntimeError(f"Missing required environment: {', '.join(missing)}")

    # Initialize PyAudio
    with no_alsa_err():
        p = pyaudio.PyAudio()

    # Get native sample rate
    device_info = p.get_default_input_device_info()
    native_rate = int(device_info['defaultSampleRate'])

    print(f"🎙️ Audio device: {device_info.get('name', 'Unknown')}", flush=True)
    print(f"🎙️ Native sample rate: {native_rate} Hz", flush=True)

    # Open audio stream
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=native_rate,
        input=True,
        frames_per_buffer=FRAME_SIZE,
    )

    print("🤖 Scrapbot V2 is active. Say the wake word.", flush=True)

    try:
        # Run the linear session loop
        await run_session_loop(stream, native_rate)
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...", flush=True)
        try:
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Scrapbot V2 stopped by user.", flush=True)
        sys.exit(0)

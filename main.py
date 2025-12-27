import asyncio
import pyaudio
import reasoner 
from listener import listen 
from config import FRAME_SIZE, PROJECT_ID 
import os
import sys
from ctypes import *
from contextlib import contextmanager

# ALSA Error Handler to suppress verbose logs
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
    except:
        yield

async def main_loop():
    # Early validation of critical environment variables
    missing = []
    if not PROJECT_ID:
        missing.append("GCP_PROJECT_ID")
    if not os.getenv("GOOGLE_APPLICATIONS_CREDENTIALS") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        missing.append("GOOGLE_APPLICATION_CREDENTIALS")
    if missing:
        raise RuntimeError(
            f"Missing required environment: {', '.join(missing)}.\n"
            "Set them in .env and ensure docker-compose.yaml includes env_file: .env"
        )

    # Suppress JACK server autostart to clean up logs
    os.environ["JACK_NO_START_SERVER"] = "1"

    with no_alsa_err():
        p = pyaudio.PyAudio()

    # 1. Identify Device
    try:
        device_info = p.get_default_input_device_info()
        native_rate = int(device_info['defaultSampleRate'])
        target_channels = 1 
        print(f"🎙️ Using Device: {device_info['name']}")
    except Exception as e:
        native_rate, target_channels = 44100, 1
        print(f"⚠️ Falling back to default specs. Error: {e}")

    # 2. Open stream
    device_index = None
    env_idx = os.getenv("AUDIO_DEVICE_INDEX")
    if env_idx:
        try:
            device_index = int(env_idx)
        except ValueError:
            device_index = None

    stream = p.open(
        format=pyaudio.paInt16,
        channels=target_channels,
        rate=native_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=FRAME_SIZE,
    )
    print("🤖 Scrapbot is active. Speak now...")

    # Create the generator once
    audio_gen = listen(stream, native_rate=native_rate)

    # Consume the generator in a loop
    while True:
        try:
            # Get the next item with a small await to ensure async cooperation
            item = await audio_gen.__anext__()
            
            # Check if it's the start session signal
            if item == "START_SESSION":
                # Clear the volume bar line to print the status message cleanly
                sys.stdout.write("\r\x1b[2K") 
                sys.stdout.flush()
                print("🛰️ Wake word detected! Starting Live Session...")
                
                # Hand over the generator to the reasoner
                await reasoner.run_live_session(audio_gen)
                
                # Flush buffers to prevent self-triggering (echo loop)
                await audio_gen.aclose() # Stop current listener and wake word worker
                try:
                    if stream.is_active():
                        n_frames = stream.get_read_available()
                        if n_frames > 0:
                            stream.read(n_frames, exception_on_overflow=False)
                except Exception:
                    pass
                
                # Restart listener
                audio_gen = listen(stream, native_rate=native_rate)

                # Clear the line again before returning to the wake-word loop
                sys.stdout.write("\r\x1b[2K")
                sys.stdout.flush()
                print("🔄 Session closed. Returning to wake-word detection.")
            # For audio bytes, just continue - the volume bar updates in listen()
            
        except StopAsyncIteration:
            break

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        # Clear the line one last time on exit
        sys.stdout.write("\r\x1b[2K")
        sys.stdout.flush()
        print("🛑 Scrapbot stopped by user.")
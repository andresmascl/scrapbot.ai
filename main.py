import asyncio
import os
import pyaudio
from ctypes import *
from contextlib import contextmanager

import listener
import reasoner

from config import FRAME_SIZE, PROJECT_ID
from app_state import listen_state
from speaker import speak

# WebSocket player interface
from player import (
    start_ws_server,
    search_and_play,
    play,
    pause,
    next_track,
)

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
# AEC device selection
# -----------------------

def find_aec_input_device(p: pyaudio.PyAudio):
    """
    Prefer PipeWire / PulseAudio echo-cancel sources.
    Falls back to default input if none found.
    """
    candidates = []

    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)

        if info.get("maxInputChannels", 0) < 1:
            continue

        name = info.get("name", "").lower()

        if any(k in name for k in (
            "echo",
            "aec",
            "cancel",
            "webrtc",
        )):
            candidates.append((i, info))

    if candidates:
        idx, info = candidates[0]
        print(
            f"🎧 Using AEC input device: "
            f"[{idx}] {info['name']} ({int(info['defaultSampleRate'])} Hz)",
            flush=True,
        )
        return idx, int(info["defaultSampleRate"])

    info = p.get_default_input_device_info()
    print(
        f"⚠️ AEC device not found. Falling back to default mic: "
        f"{info['name']} ({int(info['defaultSampleRate'])} Hz)",
        flush=True,
    )
    return info["index"], int(info["defaultSampleRate"])


# -----------------------
# Main loop
# -----------------------

async def main_loop():
    # -----------------------
    # Early validation
    # -----------------------
    if not PROJECT_ID:
        raise RuntimeError("Missing GCP_PROJECT_ID")

    if not (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or os.getenv("GOOGLE_API_KEY")
    ):
        raise RuntimeError("Missing Google credentials")

    # -----------------------
    # Start WebSocket server
    # -----------------------
    await start_ws_server()

    # -----------------------
    # Audio setup (AEC)
    # -----------------------
    p = pyaudio.PyAudio()
    device_index, native_rate = find_aec_input_device(p)

    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=native_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=FRAME_SIZE,
    )

    print("🤖 Scrapbot is active. Say the wake word.", flush=True)

    await listen_state.allow_global_wake_word()
    audio_gen = listener.listen(stream, native_rate=native_rate)

    # -----------------------
    # Event loop
    # -----------------------
    try:
        async for item in audio_gen:
            if item != "START_SESSION":
                continue

            if not await listen_state.get_global_wake_word():
                continue

            # 🔒 Block re-triggering
            await listen_state.block_global_wake_word()

            # ⏸️ CRITICAL FIX:
            # Pause playback so silence becomes observable
            try:
                await pause()
            except Exception as e:
                print(f"⚠️ Failed to pause playback: {e}", flush=True)

            print("🛰️ Listening for command...", flush=True)

            result = await reasoner.process_voice_command(audio_gen)
            print(f"📋 Reasoner returned: {result}", flush=True)

            if isinstance(result, dict):
                intent = result.get("intent")
                filter_text = result.get("filter")
                feedback = result.get("feedback")

                try:
                    if intent == "play_youtube" and filter_text:
                        print("▶️ SEARCH + PLAY", flush=True)
                        await search_and_play(filter_text)

                    elif intent == "play":
                        print("▶️ Play", flush=True)
                        await play()

                    elif intent == "pause":
                        print("⏸ Pause", flush=True)
                        await pause()

                    elif intent == "next":
                        print("⏭ Next track", flush=True)
                        await next_track()

                except Exception as e:
                    print(f"❌ Player error: {e}", flush=True)

                if feedback:
                    await speak(feedback)

            # ▶️ Resume playback after command
            try:
                await play()
            except Exception:
                pass

            print("🔄 Session complete. Re-arming wake word.", flush=True)
            await listen_state.allow_global_wake_word()

    finally:
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass

        p.terminate()


# -----------------------
# Entrypoint
# -----------------------

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("🛑 Scrapbot stopped by user.", flush=True)

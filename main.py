import asyncio
import logging
import os
import pyaudio
from ctypes import *
from contextlib import contextmanager

from config import LOG_LEVEL

# -----------------------
# Logging Setup (Pre-Init)
# -----------------------
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

import listener
import reasoner

from config import FRAME_SIZE, PROJECT_ID, AUDIO_DEVICE_INDEX
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
    if AUDIO_DEVICE_INDEX is not None:
        try:
            info = p.get_device_info_by_index(AUDIO_DEVICE_INDEX)
            if info.get("maxInputChannels", 0) > 0:
                logging.info(
                    f"🎧 Using configured input device: "
                    f"[{AUDIO_DEVICE_INDEX}] {info['name']} ({int(info['defaultSampleRate'])} Hz)"
                )
                return AUDIO_DEVICE_INDEX, int(info["defaultSampleRate"])
            else:
                logging.warning(
                    f"⚠️ Configured AUDIO_DEVICE_INDEX={AUDIO_DEVICE_INDEX} ({info['name']}) "
                    "has 0 input channels. Falling back to auto-detection."
                )
        except IOError:
            logging.warning(
                f"⚠️ Configured AUDIO_DEVICE_INDEX={AUDIO_DEVICE_INDEX} not found. "
                "Falling back to auto-detection."
            )

    candidates = []

    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)

        if info.get("maxInputChannels", 0) < 1:
            continue

        name = info.get("name", "").lower()
        if any(k in name for k in ("echo", "aec", "cancel", "webrtc")):
            candidates.append((i, info))

    if candidates:
        idx, info = candidates[0]
        logging.info(
            f"🎧 Using AEC input device: "
            f"[{idx}] {info['name']} ({int(info['defaultSampleRate'])} Hz)"
        )
        return idx, int(info["defaultSampleRate"])

    info = p.get_default_input_device_info()
    logging.warning(
        f"⚠️ AEC device not found. Falling back to default mic: "
        f"{info['name']} ({int(info['defaultSampleRate'])} Hz)"
    )
    return info["index"], int(info["defaultSampleRate"])


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

    await start_ws_server()

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

    logging.info("🤖 Scrapbot is active. Say the wake word.")

    await listen_state.allow_global_wake_word()
    audio_gen = listener.listen(stream, native_rate=native_rate)

    try:
        async for item in audio_gen:
            if item != "START_SESSION":
                continue

            if not await listen_state.get_global_wake_word():
                continue

            await listen_state.block_global_wake_word()
            logging.info("🛰️ Listening for command...")

            result = await reasoner.process_voice_command(audio_gen)
            logging.info(f"📋 Reasoner returned: {result}")

            if isinstance(result, dict):
                intent = result.get("intent")
                filter_text = result.get("filter")
                feedback = result.get("feedback")

                try:
                    if intent == "play_youtube" and filter_text:
                        logging.info("▶️ SEARCH + PLAY")
                        await search_and_play(filter_text)

                    elif intent == "resume_youtube":
                        await play()

                    elif intent == "pause_youtube":
                        await pause()

                    elif intent == "next_youtube":
                        await next_track()

                except Exception as e:
                    logging.error(f"❌ Player error: {e}")

                if feedback:
                    await speak(feedback)

            logging.info("🔄 Session complete. Re-arming wake word.")
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
        logging.info("🛑 Scrapbot stopped by user.")

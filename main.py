import asyncio
import signal

import pyaudio
from dotenv import load_dotenv

from listener import listen
from configs.listener_config import (
    AUDIO_RATE,
    CHANNELS,
    FRAME_MS,
)
import reasoner

# --------------------
# Bootstrap
# --------------------
load_dotenv()  # load .env ONCE, at entrypoint

FRAME_SIZE = int(AUDIO_RATE * FRAME_MS / 1000)

# --------------------
# Audio callback
# --------------------
async def handle_audio(wav_path: str) -> None:
    """Send recorded audio to the reasoner pipeline."""
    print(f"🧠 Sending audio to reasoner: {wav_path}")
    try:
        result = await reasoner.process_audio(wav_path)
        print(f"💡 Reasoner result: {result}")
    except Exception as exc:
        print(f"⚠️ Error processing audio: {exc}")

# --------------------
# Main
# --------------------
def main() -> None:
    p = pyaudio.PyAudio()
    stream = None

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=AUDIO_RATE,
            input=True,
            frames_per_buffer=FRAME_SIZE,
        )

        asyncio.run(listen(stream, on_audio_recorded=handle_audio))

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")

    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        p.terminate()

if __name__ == "__main__":
    main()

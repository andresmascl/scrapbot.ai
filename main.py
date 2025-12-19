import asyncio
import signal
import pyaudio
from dotenv import load_dotenv

from listener import listen, FRAME_SIZE
from config import CHANNELS

import reasoner

# --------------------
# Bootstrap
# --------------------
load_dotenv()

# --------------------
# Audio callback
# --------------------
# main.py

async def handle_audio(wav_path: str) -> None:
    """Send recorded audio to the reasoner pipeline."""
    print(f"🧠 Sending audio to reasoner: {wav_path}")
    try:
        # CHANGE THIS: from process_audio to transcribe_audio
        result, confidence = await reasoner.transcribe_audio(wav_path) 
        print(f"💡 Reasoner result: [{confidence:.1f}%] {result}")
    except Exception as exc:
        print(f"⚠️ Error processing audio: {exc}")

# --------------------
# Main
# --------------------
def main() -> None:
    p = pyaudio.PyAudio()
    stream = None

    try:
        # Detect Hardware Native Rate to avoid [Errno -9997]
        try:
            device_info = p.get_default_input_device_info()
            native_rate = int(device_info['defaultSampleRate'])
            print(f"🎙️ Using Hardware Device: {device_info['name']} at {native_rate}Hz")
        except Exception as e:
            native_rate = 44100  # Standard fallback
            print(f"⚠️ Could not detect native rate, falling back to {native_rate}Hz. Error: {e}")

        # Open stream using constants from config.py
        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=native_rate,  
            input=True,
            frames_per_buffer=FRAME_SIZE,
        )

        # Pass the native_rate to listener for internal downsampling
        asyncio.run(listen(stream, native_rate=native_rate, on_audio_recorded=handle_audio))

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        # Log actual error details for easier debugging
        import traceback
        traceback.print_exc()
        print(f"❌ Failed to initialize audio: {e}")

    finally:
        if stream is not None:
            if stream.is_active():
                stream.stop_stream()
            stream.close()
        p.terminate()

if __name__ == "__main__":
    main()
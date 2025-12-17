import asyncio
import numpy as np
import wave
import time
from openwakeword.model import Model

# --------------------
# Configuration
# --------------------
RATE = 16000
CHANNELS = 1
FRAME_MS = 30
FRAME_SIZE = int(RATE * FRAME_MS / 1000)

WAKE_KEY = "hey_mycroft"
THRESHOLD = 0.6
WAKE_RESET_THRESHOLD = 0.2
WAKE_COOLDOWN_SEC = 3.0

SILENCE_RMS = 120
SILENCE_SECONDS = 2.0
SILENCE_FRAMES_TO_STOP = int(SILENCE_SECONDS / (FRAME_MS / 1000))

# --------------------
# Wake Word Model
# --------------------
wake_model = Model()

# --------------------
# Helpers
# --------------------
def safe_rms(frame: bytes) -> float:
    samples = np.frombuffer(frame, dtype=np.int16).astype(np.float32)
    if len(samples) == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples * samples)))

def save_wav(frames, filename):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))

# --------------------
# Public API
# --------------------
async def listen(stream, on_audio_recorded=None):
    """
    Continuous wake-word listener.
    Blocks forever until cancelled.

    :param stream: PyAudio input stream
    :param on_audio_recorded: optional async callback called with WAV path
    """
    print("🎙️ Always listening (wake word + recording)…")

    recording = False
    silence_count = 0
    audio_buffer = []

    wake_armed = True
    last_record_end = 0.0

    while True:
        frame = stream.read(FRAME_SIZE, exception_on_overflow=False)
        energy = safe_rms(frame)

        bar = "#" * min(int(energy / 40), 30)
        print(f"\r🎚️ RMS={int(energy):4d} {bar:<30}", end="", flush=True)

        audio_np = np.frombuffer(frame, dtype=np.int16)
        now = time.time()

        # ---------- WAKE WORD ----------
        if not recording:
            preds = wake_model.predict(audio_np)
            score = preds.get(WAKE_KEY, 0.0)

            if score < WAKE_RESET_THRESHOLD:
                wake_armed = True

            if (
                wake_armed
                and score >= THRESHOLD
                and (now - last_record_end) > WAKE_COOLDOWN_SEC
            ):
                print(f"\n🟢 Wake word detected ({score:.2f}) — recording started")
                recording = True
                wake_armed = False
                audio_buffer.clear()
                silence_count = 0
                continue

        # ---------- RECORDING ----------
        if recording:
            audio_buffer.append(frame)

            if energy < SILENCE_RMS:
                silence_count += 1
            else:
                silence_count = 0

            if silence_count >= SILENCE_FRAMES_TO_STOP:
                filename = f"/tmp/recording_{int(time.time())}.wav"

                save_wav(audio_buffer, filename)

                print(f"\n💾 Audio saved: {filename}")
                print("🎙️ Back to wake word listening…")

                # call the async callback if provided
                if on_audio_recorded is not None:
                    await on_audio_recorded(filename)

                recording = False
                audio_buffer.clear()
                silence_count = 0
                last_record_end = time.time()

        await asyncio.sleep(0)

"""Audio handling - wake word detection, recording, VAD"""
import asyncio
import numpy as np
import torch
import pyaudio
from openwakeword.model import Model
from config import (
    WAKE_WORD, WAKE_THRESHOLD, VAD_THRESHOLD,
    SILENCE_DURATION_MS, MAX_RECORDING_SEC,
    SAMPLE_RATE, CHUNK_SIZE, WAKE_SOUND_PATH
)

# Initialize wake word model
print("Loading wake word model...", flush=True)
try:
    wake_model = Model(wakeword_models=[WAKE_WORD])
except TypeError:
    # Older API - load all default models
    wake_model = Model()

# Initialize VAD
print("Loading VAD model...", flush=True)
vad_model, utils = torch.hub.load(
    repo_or_dir='snakers4/silero-vad',
    model='silero_vad',
    force_reload=False,
    onnx=True
)
(get_speech_timestamps, _, _, _, _) = utils


async def play_beep():
    """Play wake word confirmation sound"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
            WAKE_SOUND_PATH,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
    except Exception as e:
        print(f"⚠️ Could not play beep: {e}", flush=True)


async def detect_wake_word(stream):
    """
    Listen for wake word continuously.
    Returns True when wake word is detected.
    """
    audio_buffer = bytearray()

    while True:
        # Read audio chunk
        chunk = await asyncio.to_thread(
            stream.read,
            CHUNK_SIZE,
            exception_on_overflow=False
        )

        audio_buffer.extend(chunk)

        # Keep buffer manageable
        if len(audio_buffer) > 32000:
            audio_buffer = audio_buffer[-32000:]

        # Process in 1280-sample frames (160ms at 16kHz)
        while len(audio_buffer) >= 2560:
            frame = audio_buffer[:2560]
            audio_buffer = audio_buffer[2560:]

            # Convert to numpy array
            audio_frame = np.frombuffer(frame, dtype=np.int16)

            # Get prediction
            prediction = wake_model.predict(audio_frame)
            score = prediction.get(WAKE_WORD, 0.0)

            if score > WAKE_THRESHOLD:
                print(f"🔔 Wake word detected! (score: {score:.3f})", flush=True)
                return True

        await asyncio.sleep(0.01)


def is_speech(audio_chunk):
    """Check if audio chunk contains speech using VAD"""
    audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0

    # Silero VAD needs exactly 512 samples for 16kHz
    # If chunk is larger, take the first 512 samples
    if len(audio_float32) > 512:
        audio_float32 = audio_float32[:512]
    elif len(audio_float32) < 512:
        # Pad if needed
        audio_float32 = np.pad(audio_float32, (0, 512 - len(audio_float32)))

    audio_tensor = torch.from_numpy(audio_float32)
    speech_prob = vad_model(audio_tensor, SAMPLE_RATE).item()
    return speech_prob > VAD_THRESHOLD


async def record_until_silence(stream):
    """
    Record audio until silence is detected.
    Returns audio bytes (16-bit PCM at 16kHz).
    """
    print("🎤 Recording... (speak now)", flush=True)

    frames = []
    silence_start = None
    speech_detected = False
    start_time = asyncio.get_event_loop().time()

    while True:
        # Read chunk
        chunk = await asyncio.to_thread(
            stream.read,
            CHUNK_SIZE,
            exception_on_overflow=False
        )

        frames.append(chunk)

        # Check for speech
        has_speech = is_speech(chunk)

        if has_speech:
            speech_detected = True
            silence_start = None
        else:
            if speech_detected and silence_start is None:
                silence_start = asyncio.get_event_loop().time()

        # Check silence duration
        if silence_start is not None:
            silence_duration = (asyncio.get_event_loop().time() - silence_start) * 1000
            if silence_duration > SILENCE_DURATION_MS:
                print("🔇 Silence detected, stopping recording", flush=True)
                break

        # Check max recording time
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > MAX_RECORDING_SEC:
            print("⏱️ Max recording time reached", flush=True)
            break

    if not speech_detected:
        print("⚠️ No speech detected", flush=True)
        return None

    # Combine all chunks
    audio_data = b''.join(frames)
    print(f"✅ Recorded {len(audio_data)} bytes", flush=True)
    return audio_data


def init_audio_stream():
    """Initialize PyAudio stream"""
    p = pyaudio.PyAudio()

    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )

    return p, stream

"""
Audio utility functions - pure, reusable audio processing logic.
Extracted from original listener.py and reasoner.py.
"""
import numpy as np
import torch
import threading
from openwakeword.model import Model

# Load wake word model (global, thread-safe)
print("Loading Wake Word model...", flush=True)
try:
    wake_model = Model(wakeword_models=["hey_mycroft"])
except TypeError:
    print(f"⚠️ Argument mismatch. Loading default models...", flush=True)
    wake_model = Model()

wake_model_lock = threading.Lock()

# Load Silero VAD model (global)
print("Loading Silero VAD model...", flush=True)
vad_model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-vad',
    model='silero_vad',
    force_reload=False,
    trust_repo=True
)


def detect_wake_word(audio_frame: bytes, wake_key: str = "hey_mycroft", threshold: float = 0.7) -> float:
    """
    Detect wake word in a 2560-byte audio frame (16-bit PCM, 16kHz).

    Args:
        audio_frame: 2560 bytes of 16-bit PCM audio at 16kHz
        wake_key: Wake word key (e.g., "hey_mycroft")
        threshold: Detection threshold (0.0 - 1.0)

    Returns:
        Wake word confidence score (0.0 - 1.0)
    """
    if len(audio_frame) < 2560:
        return 0.0

    audio_np = np.frombuffer(audio_frame[:2560], dtype=np.int16)

    with wake_model_lock:
        predictions = wake_model.predict(audio_np)

    return predictions.get(wake_key, 0.0)


def is_speech(audio_chunk: bytes, vad_threshold: float = 0.5) -> float:
    """
    Detect speech in a 1024-byte audio chunk using Silero VAD.

    Args:
        audio_chunk: 1024 bytes of 16-bit PCM audio at 16kHz
        vad_threshold: Speech detection threshold (0.0 - 1.0)

    Returns:
        Speech probability (0.0 - 1.0)
    """
    if len(audio_chunk) < 1024:
        return 0.0

    # Convert to float32 for Silero VAD
    audio_int16 = np.frombuffer(audio_chunk[:1024], dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0
    tensor = torch.from_numpy(audio_float32)

    try:
        speech_prob = vad_model(tensor, 16000).item()
        return speech_prob
    except Exception as e:
        print(f"⚠️ VAD error: {e}", flush=True)
        return 0.0


def reset_wake_model():
    """Reset the wake word model state."""
    with wake_model_lock:
        wake_model.reset()

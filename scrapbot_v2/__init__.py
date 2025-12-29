"""
Scrapbot V2 - Refactored linear session loop architecture.

Key improvements:
- No global state
- No nested async generators
- Linear control flow
- Sequential operations (no fire-and-forget)
- All state is local to session loop
"""

__version__ = "2.0.0"

from .session import run_session_loop
from .audio_utils import detect_wake_word, is_speech, reset_wake_model
from .llm_client import create_genai_client, transcribe_audio, get_llm_response, speak_text

__all__ = [
    "run_session_loop",
    "detect_wake_word",
    "is_speech",
    "reset_wake_model",
    "create_genai_client",
    "transcribe_audio",
    "get_llm_response",
    "speak_text",
]

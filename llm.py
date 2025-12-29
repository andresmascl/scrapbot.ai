"""LLM interactions - STT, LLM, TTS"""
import asyncio
import json
import io
import wave
from google import genai
from google.genai import types
from config import GCP_PROJECT_ID, MODEL_NAME, PROMPT_PATH


def load_system_prompt():
    """Load system prompt from PROMPT.md"""
    try:
        with open(PROMPT_PATH, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️ {PROMPT_PATH} not found", flush=True)
        return "You are a helpful assistant."


def create_client():
    """Create Google GenAI client"""
    client = genai.Client(
        vertexai=True,
        project=GCP_PROJECT_ID,
        location="us-central1"
    )
    return client


async def transcribe(client, audio_bytes):
    """
    Transcribe audio to text using Google GenAI STT.

    Args:
        client: GenAI client
        audio_bytes: Raw 16-bit PCM audio at 16kHz

    Returns:
        Transcribed text or None
    """
    print("🎧 Transcribing audio...", flush=True)

    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(16000)
        wf.writeframes(audio_bytes)

    wav_data = wav_buffer.getvalue()

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(
                    data=wav_data,
                    mime_type="audio/wav"
                ),
                "Transcribe this audio."
            ]
        )

        text = response.text.strip()
        print(f"📝 Transcript: {text}", flush=True)
        return text

    except Exception as e:
        print(f"❌ Transcription error: {e}", flush=True)
        return None


async def get_intent(client, transcript, system_prompt, session_context=None):
    """
    Get intent from LLM based on transcript.

    Args:
        client: GenAI client
        transcript: User's transcribed speech
        system_prompt: System instruction from PROMPT.md
        session_context: Previous conversation context (for resume)

    Returns:
        Parsed JSON dict or None
    """
    print("🤖 Sending to LLM...", flush=True)

    # Build prompt
    if session_context:
        full_prompt = f"{system_prompt}\n\nPrevious context:\n{session_context}\n\nUser: {transcript}"
    else:
        full_prompt = f"{system_prompt}\n\nUser: {transcript}"

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt
        )

        response_text = response.text.strip()
        print(f"📨 LLM response:\n{response_text}", flush=True)

        # Parse JSON (strip markdown if needed)
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)

        print("✅ Parsed JSON:")
        print(json.dumps(data, indent=2), flush=True)

        return data

    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse JSON: {e}", flush=True)
        return None
    except Exception as e:
        print(f"❌ LLM error: {e}", flush=True)
        return None


async def speak(text):
    """
    Speak text using TTS (espeak).

    Args:
        text: Text to speak
    """
    if not text:
        return

    print(f"🗣️ Speaking: {text}", flush=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            "espeak", text,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
        print("✅ TTS complete", flush=True)
    except Exception as e:
        print(f"⚠️ TTS error: {e}", flush=True)

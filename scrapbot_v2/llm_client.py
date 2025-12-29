"""
LLM client functions - STT, TTS, and LLM interactions.
Extracted from original reasoner.py.
"""
import asyncio
import json
import io
import wave
import os
from google import genai
from google.genai import types


def get_system_instruction() -> str:
    """Load system instruction from PROMPT.md file."""
    try:
        with open("PROMPT.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        print("⚠️ PROMPT.md not found. Using default instruction.", flush=True)
        return "You are a helpful assistant."


async def transcribe_audio(client, audio_bytes: bytes) -> str:
    """
    Transcribe audio using Google GenAI STT.

    Args:
        client: Google GenAI client instance
        audio_bytes: Raw 16-bit PCM audio at 16kHz

    Returns:
        Transcript string (empty on error)
    """
    print("✍️ Transcribing...", flush=True)
    try:
        # Convert raw PCM to WAV format
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_bytes)
            wav_data = wav_buffer.getvalue()

        # Send to GenAI for transcription
        response = await client.aio.models.generate_content(
            model=os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash-live"),
            contents=[
                types.Part(text="Transcribe the audio exactly."),
                types.Part(inline_data=types.Blob(data=wav_data, mime_type="audio/wav"))
            ]
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ STT Error: {e}", flush=True)
        return ""


async def get_llm_response(client, transcript: str, system_instruction: str) -> dict:
    """
    Get structured JSON response from LLM.

    Args:
        client: Google GenAI client instance
        transcript: User's transcribed speech
        system_instruction: System prompt for the LLM

    Returns:
        Parsed JSON dict (empty dict on error)
    """
    print(f"🤔 Thinking with LLM...", flush=True)
    try:
        response = await client.aio.models.generate_content(
            model=os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash-live"),
            contents=transcript,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )

        accumulated_response = response.text
        print("\n🤖 Raw LLM Response:")
        print(accumulated_response, flush=True)

        # Clean up JSON (strip Markdown fences)
        clean_json = accumulated_response.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)

        print("\n✅ Parsed JSON:")
        print(json.dumps(data, indent=2), flush=True)

        return data
    except json.JSONDecodeError:
        print("⚠️ Failed to parse JSON response.", flush=True)
        return {}
    except Exception as e:
        print(f"❌ LLM Error: {e}", flush=True)
        return {}


async def speak_text(text: str):
    """
    Speak text using espeak TTS.

    Args:
        text: Text to speak
    """
    print(f"🗣️ Speaking: {text}", flush=True)
    try:
        proc = await asyncio.create_subprocess_exec(
            "espeak", text,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
        print(f"✅ TTS complete", flush=True)
    except FileNotFoundError:
        print("⚠️ espeak not found", flush=True)


def create_genai_client():
    """
    Create a Google GenAI client instance.

    Returns:
        GenAI client configured with API key or GCP project
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_REGION", "us-central1")

    if api_key:
        return genai.Client(api_key=api_key, http_options={'api_version': 'v1beta1'})
    else:
        return genai.Client(project=project_id, location=location, http_options={'api_version': 'v1beta1'})

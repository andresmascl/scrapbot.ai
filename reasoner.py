import asyncio
import json
import os
import io
import wave
import numpy as np
import torch
import time
from google import genai
from google.genai import types
from config import PROJECT_ID, MODEL_NAME, SILENCE_SECONDS, VAD_THRESHOLD, TTS_REARM_DELAY_SEC
import listener  # To disable wake during TTS

# Local model / API settings (use config as primary source)
LOCATION = os.getenv("GCP_REGION", "us-central1")
MODEL_ID = os.getenv("VERTEX_MODEL_NAME", MODEL_NAME)

# Silence detection in ms
SILENCE_THRESHOLD_MS = int(float(SILENCE_SECONDS) * 1000)

# Load Silero VAD **here** (reasoner owns the VAD)
print("Loading Silero VAD in reasoner...", flush=True)
vad_model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-vad',
    model='silero_vad',
    force_reload=False,
    trust_repo=True
)


def get_system_instruction():
    try:
        with open("PROMPT.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        print("⚠️ PROMPT.md not found. Using default instruction.", flush=True)
        return "You are a helpful assistant."


async def transcribe_audio(client, audio_bytes):
    """
    Send a small WAV to the LLM STT model (using genai client).
    Returns the transcript string or empty on error.
    """
    print("✍️ Transcribing...", flush=True)
    try:
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_bytes)
            wav_data = wav_buffer.getvalue()

        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=[
                types.Part(text="Transcribe the audio exactly."),
                types.Part(inline_data=types.Blob(data=wav_data, mime_type="audio/wav"))
            ]
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ STT Error: {e}", flush=True)
        return ""


async def process_voice_command(audio_gen):
    """
    Consumes the async audio generator returned by listener.listen() after a START_SESSION.
    Records until silence is detected (using locally-run Silero VAD), transcribes audio,
    sends text to the LLM, parses JSON response and performs optional TTS feedback.

    This function *does not* perform action execution — it just returns the parsed JSON
    and plays short TTS feedback if provided by the LLM response.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta1'})
    else:
        client = genai.Client(project=PROJECT_ID, location=LOCATION, http_options={'api_version': 'v1beta1'})

    system_instruction = get_system_instruction()

    # Buffers
    frames = []
    vad_buffer = b""
    is_speaking = False
    silence_start_time = None
    listen_start_time = asyncio.get_running_loop().time()

    print("👂 Listening for command (reasoner)...", flush=True)

    try:
        async for chunk in audio_gen:
            # skip control tokens
            if isinstance(chunk, str):
                continue

            frames.append(chunk)
            vad_buffer += chunk

            # process VAD in 1024-byte frames
            while len(vad_buffer) >= 1024:
                process_chunk = vad_buffer[:1024]
                vad_buffer = vad_buffer[1024:]

                # to float32 for Silero VAD
                audio_int16 = np.frombuffer(process_chunk, dtype=np.int16)
                audio_float32 = audio_int16.astype(np.float32) / 32768.0
                tensor = torch.from_numpy(audio_float32)

                # get speech probability
                try:
                    speech_prob = vad_model(tensor, 16000).item()
                except Exception as e:
                    print(f"⚠️ VAD error: {e}", flush=True)
                    speech_prob = 0.0

                # threshold decision
                if speech_prob > float(VAD_THRESHOLD):
                    is_speaking = True
                    silence_start_time = None
                    # optional visual dot (non-essential)
                    print(".", end="", flush=True)
                else:
                    if is_speaking:
                        if silence_start_time is None:
                            silence_start_time = asyncio.get_running_loop().time()
                        elapsed_silence = (asyncio.get_running_loop().time() - silence_start_time) * 1000
                        if elapsed_silence > SILENCE_THRESHOLD_MS:
                            print("\n🛑 Silence detected. Processing...", flush=True)
                            raise StopAsyncIteration
                    else:
                        # no speech started and timeout
                        if (asyncio.get_running_loop().time() - listen_start_time) > 5.0:
                            print("\n⌛ Timeout: No speech detected.", flush=True)
                            return

    except StopAsyncIteration:
        pass
    except Exception as e:
        print(f"⚠️ Reasoner input error: {e}", flush=True)
        return

    audio_bytes = b''.join(frames)
    if not audio_bytes:
        print("⚠️ No audio captured.", flush=True)
        return

    # 1) Transcribe
    transcript = await transcribe_audio(client, audio_bytes)
    if not transcript:
        print("⚠️ No transcript.", flush=True)
        return

    print(f"\n🗣️ Transcript: {transcript}", flush=True)

    # 2) Send the transcript to the LLM for structured JSON response
    print(f"🤔 Thinking with {MODEL_ID}...", flush=True)
    try:
        # Generate content with preference for JSON structured output
        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=transcript,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )

        accumulated_response = response.text

        print("\n🤖 Raw LLM Response:")
        print(accumulated_response, flush=True)

        # Try to extract JSON (strip Markdown fences if present)
        clean_json = accumulated_response.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(clean_json)
            print("\n✅ Parsed JSON:")
            print(json.dumps(data, indent=2), flush=True)

            # Clear audio and event queues after JSON response
            audio_cleared = 0
            event_cleared = 0
            try:
                if hasattr(listener.rearm_wake_word, '_audio_queue'):
                    while not listener.rearm_wake_word._audio_queue.empty():
                        try:
                            listener.rearm_wake_word._audio_queue.get_nowait()
                            audio_cleared += 1
                        except:
                            break
                if hasattr(listener.rearm_wake_word, '_event_queue'):
                    while not listener.rearm_wake_word._event_queue.empty():
                        try:
                            listener.rearm_wake_word._event_queue.get_nowait()
                            event_cleared += 1
                        except:
                            break
                if audio_cleared > 0 or event_cleared > 0:
                    print(f"🗑️ Cleared {audio_cleared} audio chunks and {event_cleared} events after JSON response", flush=True)
            except Exception as e:
                print(f"⚠️ Error clearing queues after JSON: {e}", flush=True)

            # optional feedback TTS if present
            if "feedback" in data and data["feedback"]:
                text = data["feedback"]
                print(f"🗣️ Speaking: {text}", flush=True)

                # Disable wake word detection immediately (no delay yet)
                print(f"🔇 Disabling wake detection before TTS to prevent loopback", flush=True)
                print(f"🔀 Setting global_wake_allowed = False (before TTS)", flush=True)
                listener.global_wake_allowed = False  # Disable immediately

                try:
                    proc = await asyncio.create_subprocess_exec(
                        "espeak", text, stderr=asyncio.subprocess.DEVNULL
                    )
                    await proc.wait()  # WAIT for TTS to complete
                    print(f"✅ TTS complete", flush=True)
                except FileNotFoundError:
                    pass

                # NOW start the rearm delay timer after TTS has finished
                print(f"🔧 Starting {TTS_REARM_DELAY_SEC}s rearm delay after TTS completion", flush=True)
                listener.rearm_wake_word(delay=TTS_REARM_DELAY_SEC, clear_queue=True)

            # return parsed data for further action (executor)
            return data

        except json.JSONDecodeError:
            print("⚠️ Failed to parse JSON response.", flush=True)
    except Exception as e:
        print(f"❌ LLM Error: {e}", flush=True)

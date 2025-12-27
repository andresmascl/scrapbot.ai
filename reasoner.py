import asyncio
import json
import os
import sys
import subprocess
import io
import wave
import numpy as np
import torch
from google import genai
from google.genai import types
from config import PROJECT_ID
import listener  # Access vad_model from listener

# Configuration
LOCATION = "us-central1"
MODEL_ID = "gemini-2.0-flash-exp"
SILENCE_THRESHOLD_MS = 1500  # Stop streaming after 1.5s of silence

def get_system_instruction():
    try:
        with open("PROMPT.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        print("⚠️ PROMPT.md not found. Using default instruction.")
        return "You are a helpful assistant."

async def transcribe_audio(client, audio_bytes):
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
        print(f"⚠️ STT Error: {e}")
        return ""

async def run_live_session(audio_gen):
    """
    Records audio, transcribes it using Google STT, and sends text to LLM.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"🔑 Using Google AI Studio API Key with {MODEL_ID}...", flush=True)
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta1'})
    else:
        print(f"⚡ Connecting to Vertex AI with {MODEL_ID}...", flush=True)
        client = genai.Client(project=PROJECT_ID, location=LOCATION, http_options={'api_version': 'v1beta1'})

    system_instruction = get_system_instruction()
    
    # VAD State
    frames = []
    silence_start_time = None
    is_speaking = False
    vad_buffer = b""
    
    print("👂 Listening...", flush=True)

    try:
        async for chunk in audio_gen:
            if isinstance(chunk, str):
                continue
            frames.append(chunk)
            vad_buffer += chunk
            
            # Local VAD Logic to detect "Stop"
            while len(vad_buffer) >= 1024:
                process_chunk = vad_buffer[:1024]
                vad_buffer = vad_buffer[1024:]

                # Convert int16 bytes to float32 tensor for Silero VAD
                audio_int16 = np.frombuffer(process_chunk, dtype=np.int16)
                audio_float32 = audio_int16.astype(np.float32) / 32768.0
                tensor = torch.from_numpy(audio_float32)
                
                # Get speech probability
                speech_prob = listener.vad_model(tensor, 16000).item()
                
                if speech_prob > 0.5:
                    is_speaking = True
                    silence_start_time = None
                    sys.stdout.write(".") # Visual feedback for speech
                    sys.stdout.flush()
                else:
                    if is_speaking: # Only count silence if we have started speaking
                        if silence_start_time is None:
                            silence_start_time = asyncio.get_running_loop().time()
                        
                        elapsed_silence = (asyncio.get_running_loop().time() - silence_start_time) * 1000
                        if elapsed_silence > SILENCE_THRESHOLD_MS:
                            print("\n🛑 Silence detected. Processing...", flush=True)
                            raise StopAsyncIteration
    except StopAsyncIteration:
        pass

    audio_bytes = b''.join(frames)
    if not audio_bytes:
        return

    # 1. Transcribe
    transcript = await transcribe_audio(client, audio_bytes)
    if not transcript:
        print("⚠️ No speech detected.")
        return
    print(f"🗣️ Transcript: {transcript}")

    # 2. Send to LLM
    print(f"🤔 Thinking with {MODEL_ID}...", flush=True)
    try:
        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=transcript,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )
        
        accumulated_response = response.text

        # Parse and Print JSON
        print("\n🤖 Raw LLM Response:")
        print(accumulated_response)
        
        try:
            # Clean up markdown code blocks if present
            clean_json = accumulated_response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            print("\n✅ Parsed JSON:")
            print(json.dumps(data, indent=2))
            
            if "feedback" in data:
                text = data["feedback"]
                print(f"🗣️ Speaking: {text}")
                try:
                    proc = await asyncio.create_subprocess_exec(
                        "espeak", text, stderr=asyncio.subprocess.DEVNULL
                    )
                    await proc.wait()
                except FileNotFoundError:
                    pass
        except json.JSONDecodeError:
            print("⚠️ Failed to parse JSON response.")
    except Exception as e:
        print(f"❌ LLM Error: {e}")
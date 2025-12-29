"""
Linear session loop - single function owns entire lifecycle.
No generators, no nested async, no global state.

Key design principles:
1. All state is local to the function
2. No async sub-functions that fire-and-forget
3. Sequential phases: wake → record → process → speak → reset
4. Reuses old functions as simple building blocks
"""
import asyncio
import audioop
import subprocess
import time
from .config import (
    WAKE_KEY,
    WAKE_THRESHOLD,
    WAKE_COOLDOWN_SEC,
    VAD_THRESHOLD,
    SILENCE_THRESHOLD_MS,
    TTS_REARM_DELAY_SEC,
    STREAM_DRAIN_SEC,
    READ_CHUNK_SIZE,
    NO_SPEECH_TIMEOUT_SEC,
    MAX_RECORDING_SEC,
    WAKE_SOUND_PATH,
)
from .audio_utils import detect_wake_word, is_speech, reset_wake_model
from .llm_client import (
    create_genai_client,
    get_system_instruction,
    transcribe_audio,
    get_llm_response,
    speak_text,
)


async def run_session_loop(stream, native_rate: int = 16000):
    """
    Main session loop - owns entire session lifecycle.

    This function runs continuously and handles:
    1. Wake word detection (inline, not background task)
    2. Audio recording until silence (no generator)
    3. Transcription and LLM processing
    4. TTS playback
    5. Stream draining and rearm

    All state is local - no global variables, no shared generators.

    Args:
        stream: PyAudio stream object
        native_rate: Native sample rate of the audio stream
    """
    print(f"🎙️ Session loop starting — resampling {native_rate}Hz → 16kHz", flush=True)

    # Initialize clients and models
    client = create_genai_client()
    system_instruction = get_system_instruction()
    reset_wake_model()

    # Local state (not global!)
    session_state = {
        'wake_allowed': True,
        'in_session': False,
        'last_wake_time': 0.0,
    }

    # Audio buffers for wake detection
    wake_buffer = bytearray()
    resample_state = None

    # Main loop - runs forever
    while True:
        try:
            # ==========================================
            # PHASE 1: LISTEN FOR WAKE WORD (INLINE)
            # ==========================================
            if session_state['wake_allowed'] and not session_state['in_session']:
                # Read audio from stream
                raw_audio = await asyncio.to_thread(
                    stream.read,
                    READ_CHUNK_SIZE,
                    exception_on_overflow=False,
                )

                # Resample to 16kHz
                resampled, resample_state = audioop.ratecv(
                    raw_audio, 2, 1, native_rate, 16000, resample_state
                )

                # Add to wake detection buffer
                wake_buffer.extend(resampled)

                # Keep buffer manageable (2 seconds of audio)
                if len(wake_buffer) > 32000:
                    wake_buffer = wake_buffer[-32000:]

                # Process wake detection in 2560-byte frames
                while len(wake_buffer) >= 2560:
                    frame = bytes(wake_buffer[:2560])
                    wake_buffer = wake_buffer[2560:]

                    # Check cooldown
                    now = time.time()
                    if now < session_state['last_wake_time'] + WAKE_COOLDOWN_SEC:
                        continue

                    # Detect wake word (sync function, no threading)
                    score = detect_wake_word(frame, WAKE_KEY, WAKE_THRESHOLD)

                    if score > WAKE_THRESHOLD:
                        print(f"🔔 Wake word detected! Score: {score:.3f}", flush=True)

                        # Play confirmation sound (don't await, fire-and-forget is OK here)
                        asyncio.create_task(_play_wake_sound())

                        # Update state
                        session_state['wake_allowed'] = False
                        session_state['in_session'] = True
                        session_state['last_wake_time'] = now

                        # Clear wake buffer
                        wake_buffer.clear()

                        # Break out of wake detection to start recording
                        break

            # ==========================================
            # PHASE 2: RECORD COMMAND (INLINE)
            # ==========================================
            if session_state['in_session']:
                print("👂 Listening for command...", flush=True)

                # Recording state (local, not global)
                frames = []
                vad_buffer = bytearray()
                is_speaking = False
                silence_start_time = None
                recording_start_time = asyncio.get_running_loop().time()

                # Record until silence or timeout
                while True:
                    # Read audio chunk
                    raw_audio = await asyncio.to_thread(
                        stream.read,
                        READ_CHUNK_SIZE,
                        exception_on_overflow=False,
                    )

                    # Resample to 16kHz
                    resampled, resample_state = audioop.ratecv(
                        raw_audio, 2, 1, native_rate, 16000, resample_state
                    )

                    # Store for transcription
                    frames.append(resampled)
                    vad_buffer.extend(resampled)

                    # Process VAD in 1024-byte chunks
                    while len(vad_buffer) >= 1024:
                        vad_chunk = bytes(vad_buffer[:1024])
                        vad_buffer = vad_buffer[1024:]

                        # Check for speech (sync function)
                        speech_prob = is_speech(vad_chunk, VAD_THRESHOLD)

                        if speech_prob > VAD_THRESHOLD:
                            # Speech detected
                            is_speaking = True
                            silence_start_time = None
                            print(".", end="", flush=True)
                        else:
                            # Silence detected
                            if is_speaking:
                                if silence_start_time is None:
                                    silence_start_time = asyncio.get_running_loop().time()
                                elapsed_silence_ms = (
                                    asyncio.get_running_loop().time() - silence_start_time
                                ) * 1000
                                if elapsed_silence_ms > SILENCE_THRESHOLD_MS:
                                    print("\n🛑 Silence detected. Processing...", flush=True)
                                    break
                            else:
                                # No speech yet - check timeout
                                elapsed = asyncio.get_running_loop().time() - recording_start_time
                                if elapsed > NO_SPEECH_TIMEOUT_SEC:
                                    print("\n⌛ Timeout: No speech detected.", flush=True)
                                    session_state['in_session'] = False
                                    session_state['wake_allowed'] = True
                                    break

                    # Check maximum recording duration
                    elapsed = asyncio.get_running_loop().time() - recording_start_time
                    if elapsed > MAX_RECORDING_SEC:
                        print("\n⏱️ Maximum recording duration reached.", flush=True)
                        break

                    # If silence detected in VAD loop, break
                    if is_speaking and silence_start_time and (
                        asyncio.get_running_loop().time() - silence_start_time
                    ) * 1000 > SILENCE_THRESHOLD_MS:
                        break

                # Skip processing if no speech detected
                if not is_speaking:
                    session_state['in_session'] = False
                    session_state['wake_allowed'] = True
                    continue

                # Combine all frames into single audio buffer
                audio_bytes = b''.join(frames)

                if not audio_bytes:
                    print("⚠️ No audio captured.", flush=True)
                    session_state['in_session'] = False
                    session_state['wake_allowed'] = True
                    continue

                # ==========================================
                # PHASE 3: TRANSCRIBE & PROCESS (REUSED)
                # ==========================================
                transcript = await transcribe_audio(client, audio_bytes)

                if not transcript:
                    print("⚠️ No transcript.", flush=True)
                    session_state['in_session'] = False
                    session_state['wake_allowed'] = True
                    continue

                print(f"\n🗣️ Transcript: {transcript}", flush=True)

                # Get LLM response
                response_data = await get_llm_response(client, transcript, system_instruction)

                if not response_data:
                    print("⚠️ No response from LLM.", flush=True)
                    session_state['in_session'] = False
                    session_state['wake_allowed'] = True
                    continue

                # ==========================================
                # PHASE 4: SPEAK RESPONSE (INLINE)
                # ==========================================
                if "feedback" in response_data and response_data["feedback"]:
                    feedback_text = response_data["feedback"]

                    # Wake detection stays disabled during TTS
                    await speak_text(feedback_text)

                    # ==========================================
                    # PHASE 5: DRAIN & REARM (SEQUENTIAL)
                    # ==========================================
                    print(f"🧹 Draining stream buffer...", flush=True)
                    await _drain_stream(stream, STREAM_DRAIN_SEC, READ_CHUNK_SIZE)

                    print(f"⏳ Waiting {TTS_REARM_DELAY_SEC}s before re-enabling wake detection...", flush=True)
                    await asyncio.sleep(TTS_REARM_DELAY_SEC)

                # Reset session state
                session_state['in_session'] = False
                session_state['wake_allowed'] = True
                print("🔓 Wake word detection re-enabled.", flush=True)

        except KeyboardInterrupt:
            print("\n👋 Shutting down session loop...", flush=True)
            break
        except Exception as e:
            print(f"❌ Error in session loop: {e}", flush=True)
            # Reset state on error
            session_state['in_session'] = False
            session_state['wake_allowed'] = True
            await asyncio.sleep(1.0)  # Brief pause before retrying


async def _play_wake_sound():
    """Play wake confirmation sound (fire-and-forget is OK here)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
            WAKE_SOUND_PATH,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        await proc.wait()
    except Exception:
        pass


async def _drain_stream(stream, duration_sec: float, chunk_size: int):
    """
    Drain audio stream buffer to remove TTS feedback.

    Args:
        stream: PyAudio stream
        duration_sec: How long to drain (seconds)
        chunk_size: Bytes per read
    """
    drain_chunks = int(duration_sec * 16000 / chunk_size)
    try:
        for _ in range(drain_chunks):
            await asyncio.to_thread(
                stream.read,
                chunk_size,
                exception_on_overflow=False
            )
    except Exception as e:
        print(f"⚠️ Error draining stream: {e}", flush=True)

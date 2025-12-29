"""
Scrapbot.ai - Main entry point
Follows the linear flow from 10KFEETVIEW.mmd
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from audio import detect_wake_word, play_beep, record_until_silence, init_audio_stream
from llm import create_client, transcribe, get_intent, speak, load_system_prompt
from actions import execute_action
from config import SESSION_TIMEOUT_HOURS, GCP_PROJECT_ID


# Session state
session_context = None
session_start_time = None


def is_context_flush(transcript):
    """
    Check if transcript contains context flush keywords.
    Returns True if user wants to start a new session.
    """
    flush_keywords = ["new session", "start over", "reset", "clear context"]
    transcript_lower = transcript.lower()

    for keyword in flush_keywords:
        if keyword in transcript_lower:
            return True

    return False


async def main():
    """Main loop following 10KFEETVIEW.mmd"""
    global session_context, session_start_time

    # Validate environment
    if not GCP_PROJECT_ID:
        raise RuntimeError("Missing GCP_PROJECT_ID environment variable")

    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        raise RuntimeError("Missing GOOGLE_APPLICATION_CREDENTIALS environment variable")

    print("🤖 Scrapbot.ai starting...", flush=True)

    # Initialize
    client = create_client()
    system_prompt = load_system_prompt()
    p, stream = init_audio_stream()

    print("✅ Ready! Listening for wake word...", flush=True)

    try:
        while True:
            # === PHASE 1: Listen for wake word ===
            await detect_wake_word(stream)

            # === PHASE 2: Play beep ===
            await play_beep()

            # === PHASE 3: Record audio ===
            audio_data = await record_until_silence(stream)

            if not audio_data:
                print("⏭️ No audio recorded, going back to listening", flush=True)
                continue

            # === PHASE 4: Transcribe (STT) ===
            transcript = await transcribe(client, audio_data)

            if not transcript:
                print("⏭️ No transcript, going back to listening", flush=True)
                continue

            # === PHASE 5: Check for context flush ===
            if is_context_flush(transcript):
                print("🆕 Starting new session", flush=True)
                session_context = None
                session_start_time = datetime.now()
            else:
                if session_context:
                    print("🔄 Resuming session with context", flush=True)
                else:
                    print("🆕 Starting new session (no context)", flush=True)
                    session_start_time = datetime.now()

            # === PHASE 6: Get intent from LLM ===
            intent_data = await get_intent(client, transcript, system_prompt, session_context)

            if not intent_data:
                print("⏭️ No intent data, going back to listening", flush=True)
                continue

            # Update session context for future resume
            if session_context:
                session_context += f"\nUser: {transcript}\nAssistant: {json.dumps(intent_data)}"
            else:
                session_context = f"User: {transcript}\nAssistant: {json.dumps(intent_data)}"

            # === PHASE 7: Execute automation ===
            await execute_action(intent_data)

            # === PHASE 8: Speak feedback (TTS) ===
            feedback = intent_data.get("feedback", "")
            if feedback:
                await speak(feedback)

            # === PHASE 9: Check session timeout (7 hours) ===
            if session_start_time:
                elapsed = datetime.now() - session_start_time
                if elapsed > timedelta(hours=SESSION_TIMEOUT_HOURS):
                    print("⏰ Session timeout reached, clearing context", flush=True)
                    session_context = None
                    session_start_time = None

            print("✅ Ready! Listening for wake word...", flush=True)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...", flush=True)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    asyncio.run(main())

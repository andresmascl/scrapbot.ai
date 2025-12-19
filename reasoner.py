# reasoner.py
import os
import asyncio
from google.cloud.speech_v2.types import cloud_speech
# Import the ALREADY initialized client from config
from config import speech_client, PROJECT_ID, REGION

async def transcribe_audio(wav_path: str):
    if not os.path.exists(wav_path):
        print(f"⚠️ File not found: {wav_path}")
        return "", 0.0

    try:
        with open(wav_path, "rb") as f:
            audio_content = f.read()

        # The V2 Recognizer path
        recognizer_path = f"projects/{PROJECT_ID}/locations/{REGION}/recognizers/_"

        # MATCHING THE CURL SUCCESS: 
        # 1. Single language code 
        # 2. auto_decoding_config (required for V2 regional)
        config = cloud_speech.RecognitionConfig(
			model="chirp_3",  # Updated from chirp_2
			language_codes=["es-US"], 
			auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
			features=cloud_speech.RecognitionFeatures(
				enable_automatic_punctuation=True,
			),
		)

        request = cloud_speech.RecognizeRequest(
            recognizer=recognizer_path,
            config=config,
            content=audio_content,
        )

        print(f"📡 Sending audio to Chirp 3 ({REGION})...")
        
        # Use a shorter timeout to catch hangs faster
        # asyncio.to_thread is correct for blocking gRPC calls
        response = await asyncio.wait_for(
            asyncio.to_thread(speech_client.recognize, request=request),
            timeout=10.0 
        )

        if not response.results:
            return "", 0.0

        result = response.results[0]
        transcript = result.alternatives[0].transcript
        confidence = result.alternatives[0].confidence * 100
        
        print(f"✅ Success: {transcript}")
        return transcript, confidence

    except asyncio.TimeoutError:
        print("🛑 STT Timeout: The gRPC connection is likely blocked by a firewall or proxy.")
        return "TIMEOUT_ERROR", 0.0
    except Exception as e:
        print(f"❌ STT V2 Error: {e}")
        return "", 0.0
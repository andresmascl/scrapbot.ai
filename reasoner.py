from google.cloud import speech_v1p1beta1 as speech
import vertexai
from vertexai.generative_models import GenerativeModel
from configs.reasoner_config import (
	speech_client,
	MODEL_NAME,
)

# --------------------
# STT
# --------------------
async def transcribe_audio(wav_path: str) -> str:
	"""
	Transcribe a local WAV file using Google Speech-to-Text.
	"""
	with open(wav_path, "rb") as f:
		content = f.read()

	audio = speech.RecognitionAudio(content=content)

	config = speech.RecognitionConfig(
		encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
		sample_rate_hertz=16000,
		language_code="es-CL",
	)

	response = speech_client.recognize(
		config=config,
		audio=audio,
	)

	return " ".join(
		result.alternatives[0].transcript
		for result in response.results
	)

# --------------------
# LLM Reasoning
# --------------------
async def reason_text(text: str) -> str:
    model = GenerativeModel(MODEL_NAME)

    prompt = (
        "Extract intent and entities from the following text "
        "and return JSON only.\n\n"
        f"Text: {text}"
    )

    response = model.generate_content(
        prompt,
        generation_config={
            "max_output_tokens": 256,
            "temperature": 0.2,
        },
    )

    return response.text

# --------------------
# Pipeline
# --------------------
async def process_audio(wav_path: str) -> str:
    """
    Full pipeline:
    WAV → Speech-to-Text → LLM reasoning
    """
    transcript = await transcribe_audio(wav_path)
    print(f"📝 Transcript: {transcript}")

    reasoning = await reason_text(transcript)
    print(f"🤖 Reasoning result:\n{reasoning}")

    return reasoning

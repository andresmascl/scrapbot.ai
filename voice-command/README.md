# Voice Command → Whisper Transcription

This module records a single user voice command after the wake word triggers
and sends it to **OpenAI Whisper (API)** for transcription.

## Features
- 5-second voice capture (configurable)
- Saves audio as `command.wav`
- Uses OpenAI Whisper for accurate transcription
- Prints plain text output to be used by any agent

## Installation

```
pip install -r requirements.txt
```

Set your OpenAI key:

```
export OPENAI_API_KEY="your-key-here"
```

## Usage

```
python3 voice_to_text.py
```

You'll see:

```
🎤 Listening for command...
```

Then the script will:
1. Capture your voice
2. Upload audio to Whisper API
3. Print the decoded text

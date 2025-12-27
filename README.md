# Scrapbot.ai

**Scrapbot.ai** is a local-first, Linux-based voice assistant with cloud LLM support focused on **continuous listening**, **wake word detection**, **speech stop detection**, **speech understanding**, **intent detection**, **General Query Replies**, **TTS Transformation**, and **Local Browser Automation** designed to run entirely on old laptops, and Dockerized to ensure OS agnosticism.

The project is intentionally minimal and modular, with a strong emphasis on **real-time audio processing**, **AI-driven intent recognition**, and **developer ownership**.



## Instructions For Codingn Agents:  
If you're **Coding Agent** working for this project, refer to [AGENTS.md](./AGENTS.md) before reading below information.

## Quick Start

```bash
make help      # Show available commands
make build     # Build the Docker image
make up        # Start container in background
make run       # Start container in foreground (see logs)
make down      # Stop and remove container
make logs      # Follow container logs
make shell     # Open terminal inside container
make clean     # Remove image and cached volumes
```


## What Scrapbot.ai Does

- Continuously listens to microphone input
- Detects a custom wake word ("hey mycroft")
- Records speech and waits for silence
- Converts speech to text (STT)
- Infers user intent from a predefined intent list
- Produces structured JSON responses
- Replies to the user using local neural text-to-speech (TTS)


## What Scrapbot.ai Does NOT Do (yet)

- Browser automation
- Custom Scrapbot.ai wakeword
- Smart-home integrations
- Mobile app
- Always-on cloud dependency
- Consumer assistant UI

Scrapbot.ai is a **voice processing and intent inference engine** (for now), not a full Alexa replacement.



## Voice Processing Pipeline

```
Continuous listening (local) 
  ↓
Wake word detection (local) 
  ↓
Silence detection (local) 
  ↓
Speech-to-Text (STT) (cloud) 
  ↓
Intent recognition (cloud) 
  ↓
JSON response 
  ↓
Text-to-Speech (TTS) (local)
```



## Project Structure

```
SCRAPBOT.AI/
├── configs/
│   ├── listener_config.py
│   └── reasoner_config.py
├── creds/
├── tests/
├── .env
├── .env.demo
├── docker-compose.yaml
├── Dockerfile
├── listener.py
├── main.py
├── Makefile
├── README.md
├── reasoner.py
└── requirements.txt
```

**Key Files:**
- `listener.py` - Wake word detection, Audio capture, and Silence detection
- `reasoner.py` - Text to Speech, Intent recognition, and Response generation
- `main.py` - Main entry point and event loop orchestration
- `configs/listener_config.py` - Audio and Wake Word settings
- `configs/reasoner_config.py` - NLP pipeline configuration



## Tech Stack

**Audio & Runtime**
- Python 3.10+
- AsyncIO - event-driven architecture
- PyAudio - real-time microphone streaming
- WebRTC VAD - silence detection

**AI / NLP**
- Sentence Transformers - wake word & semantic intent matching
- Google Speech-to-Text - speech recognition
- Google Dialogflow - intent classification and NLP

**Voice Output**
- Coqui TTS - local neural text-to-speech (CPU-based)

**Infrastructure**
- Docker - containerized deployment
- Linux (Debian / Ubuntu) - primary platform


## Configuration

The system uses a modular configuration approach:

- `listener_config.py` - audio capture, wake word detection settings
- `reasoner_config.py` - intent recognition, NLP pipeline settings
- `.env` - API keys and secrets (not committed)
- `.env.demo` - template for required environment variables



## Example Flow

1. System continuously listens to audio input
2. User says: "hey mycroft, what time is it"
3. Wake word is detected via embeddings
4. Speech is recorded until silence is detected
5. Audio is transcribed to text
6. Intent is inferred and returned as structured JSON
7. A spoken response is generated via TTS



## Hardware Requirements

- Any Linux laptop or PC
- x86_64 CPU
- 4-8 GB RAM recommended
- Microphone
- Speakers or headphones



## Docker Deployment

Run Scrapbot.ai in a container:

```bash
docker-compose up
```

This approach ensures consistent behavior across different environments.


## Project Status

**Early-stage / experimental**

Core pipeline defined. APIs and interfaces may evolve.

**Todo:**
- Add sound to indicate it has detected the wake word
- Add sound to indicate it's sending the audio to Google STT
- System can ask for user's reiteration when unsure
- Intent library
- Browser control automation
- Custom wake word training
- Audio stream instead of audio file to make it go faster ⚡



## Philosophy

- **Local-first** - you own the system
- **Explicit over magical** - transparent processing
- **Minimal dependencies** - fewer moving parts
- **Composable** - easy to extend with new intents


## Architecture

The system follows a clean separation of concerns:

- `listener.py` handles all audio input, wake word detection, and silence detection
- `reasoner.py` processes transcribed text, classifies intents, generates responses
- `main.py` orchestrates the pipeline and manages the event loop

This modular design makes it easy to swap components or extend functionality.


## License

MIT License

Vibe coded with free chatgpt version GPT-5.2.


## Audience

- Backend engineers
- Applied AI / NLP engineers
- Linux users
- Developers interested in real-time audio systems

**If you want a consumer assistant, buy one.**  
**If you want to understand and control the pipeline, deploy Scrapbot.ai.**
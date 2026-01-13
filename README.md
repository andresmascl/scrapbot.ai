# Scrapbot.ai

**Scrapbot.ai** is a local-first, Linux-native voice assistant with cloud LLM support, designed for developers who want full control over the voice pipeline.

It focuses on continuous listening, wake-word detection, speech stop detection, speech understanding, intent detection, structured JSON reasoning, local TTS, and real browser automation — all running directly on the host OS, without containers.

The project is intentionally minimal, explicit, and modular, prioritizing real-time audio processing, predictable control flow, and developer ownership over black-box convenience.

---

## Instructions for Coding Agents

If you are a **coding agent** working on this project, read [AGENTS.md](./AGENTS.md) first.

---

## Quick Start (Host-Native)

Scrapbot is designed to run **directly on Linux**, not inside Docker.

### Prerequisites

- Linux (Debian / Ubuntu recommended)
- Python 3.12+
- Microphone + speakers
- Internet access (for cloud STT / LLM)

### Setup

```bash
make venv
make deps
make browsers
make run

# Available Commands

make help       # Show available commands
make venv       # Create Python virtual environment
make deps       # Install Python dependencies
make browsers   # Install Playwright Chromium
make run        # Run Scrapbot
make clean      # Remove venv and caches
```



## Features

### What Scrapbot.ai Does

- Continuously listens to microphone input
- Detects a generic wake word ("hey Mycroft")
- Buffers and records speech until silence is detected
- Converts speech to text (cloud STT)
- Infers user intent using a Google LLM (Vertex Multimodal Live AI)
- Produces structured JSON intent responses
- Executes actions based on intent, including YouTube search and playback via a real browser
- Replies using local neural TTS

### What Scrapbot.ai Does NOT Do (yet)

- Smart-home integrations
- Multi-turn memory beyond a session
- Custom "Hey Scrapbot" wake word (listed as a TODO)
- Mobile app / LAN server integration (listed as a TODO)
- Host volume control (listed as a TODO)

For current changes and roadmap, see [CHANGELOG.md](./CHANGELOG.md).

---

## Voice Processing Pipeline

Continuous listening (local)
↓
Wake word detection (local)
↓
Silence detection (local)
↓
Intent reasoning + Speech-to-Text (cloud LLM)
↓
Structured JSON response
↓
Text-to-Speech (local)
↓
Local action execution

## Browser Automation

Scrapbot is meant to control a local Brave browser instance by establishing a socket connection with the browser through a chrome extension.

**Current capabilities:**
- Open YouTube
- Type search queries
- Click and play results
- Keep the browser session alive across commands

This runs **directly on the host OS**, not inside Docker.

---

## Project Structure

SCRAPBOT.AI/
├── creds/
├── chrome-extension/
├── .env
├── .env.demo
├── listener.py
├── main.py
├── browser.py
├── app_state.py
├── Makefile
├── README.md
├── reasoner.py
├── requirements.txt
├── config.py
├── speaker.py
├── asound.conf
├── PROMPT.md
└── SEQUENCEDIAGRAM.md

### Key Files

- `listener.py` — audio capture, wake-word detection, silence detection
- `reasoner.py` — STT handling, intent reasoning, JSON responses
- `browser.py` — Playwright browser control
- `app_state.py` — shared async application state
- `main.py` — event loop and orchestration
- `Makefile` — environment setup and execution
- `chrome-extension/` — Chrome extension files for browser automation
- `config.py` — runtime constants and defaults
- `speaker.py` — Text-to-Speech (TTS) output
- `asound.conf` — ALSA sound server configuration for audio input/output
- `PROMPT.md` — Prompt file sent to Vertex Multimodal Live AI
- `SEQUENCEDIAGRAM.md` — General system workflow diagram

---

## Tech Stack

### Audio & Runtime
- Python 3.12+
- `asyncio` — event-driven core
- PyAudio — real-time microphone streaming
- Silero VAD — silence detection
- OpenWakeWord — wake-word inference

### AI / NLP
- Google Speech-to-Text (cloud)
- Google Vertex Multimodal Live AI (intent reasoning)
- Structured JSON intent contracts

### Voice Output
- Local TTS (CPU-based)

### Browser Automation
- Brave (bundled, non-headless)

### Platform
- Linux (Debian / Ubuntu)

---

## Configuration

Configuration is explicit and file-based:

- `.env` — credentials and runtime settings (not committed)
- `.env.demo` — template for required variables
- `config.py` — runtime constants and defaults

### Environment Variables

**Core Settings:**
- `GCP_PROJECT_ID`: Your Google Cloud Project ID.
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to your service account key.

**Audio & System:**
- `AUDIO_DEVICE_INDEX`: (Optional) Force a specific input device index (integer). If not set or invalid, Scrapbot auto-detects the best AEC microphone.
- `LOG_LEVEL`: Set logging verbosity (e.g., `DEBUG`, `INFO`, `WARNING`). Default is `INFO`.
- `ENABLE_VOLUME_BAR`: Set to `1` to show the real-time volume meter in the terminal.

---

## Example Flow

1. System listens continuously
2. User says:  
   **“hey mycroft, play classical music”**
3. Wake word is detected
4. Speech is buffered until silence
5. Audio is transcribed
6. Intent is inferred and returned as JSON:

```json
{
  "intent": "play_youtube",
  "filter": "classical music",
  "confidence": 0.9
}
```

- Browser opens and plays music
- Wake word is re-armed

---

## Hardware Requirements

- Any Linux laptop or PC
- x86_64 CPU
- 4–8 GB RAM recommended
- Microphone
- Speakers or headphones

Designed to run on **old laptops**.

---

## Docker Status

⚠️ **Docker is no longer the primary deployment path.**

Scrapbot runs best **host-native**, due to:
- Real-time audio requirements
- GUI browser automation
- Lower latency
- Fewer system integration issues

Docker support may return later for **headless / server use-cases**.

---

## Project Status

**Early-stage but functional**

Core pipeline is stable. Interfaces may evolve.

### Todo

- [ ] Implement Volume Control
- [ ] Implement Custom "Hey Scrapbot" Wakeword
- [ ] Update Scrapbot.ai Voice to be More Natural
- [ ] Implement LAN server to communicate with the bot?
- [ ] Audible wake-word confirmation sound
- [ ] Confidence-based clarification prompts
- [ ] Expanded intent library
- [ ] Multi-command sessions
- [ ] Streaming STT for lower latency

---

## Philosophy

- **Local-first** — you own the system
- **Explicit over magical** — no hidden behavior
- **Minimal dependencies** — fewer failure modes
- **Composable** — easy to extend with new intents
- **Engineer-oriented** — transparency over polish

---

## Architecture

Clear separation of concerns:

- `listener.py` — audio + wake word
- `reasoner.py` — reasoning + intent
- `browser.py` — execution layer
- `main.py` — orchestration

This makes the system easy to debug, extend, or replace piece-by-piece.
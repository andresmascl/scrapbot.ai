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
- Detects a wake word ("hey mycroft")
- Buffers and records speech until silence is detected
- Converts speech to text (cloud STT)
- Infers user intent using an LLM
- Produces structured JSON intent responses
- Executes actions based on intent
- Replies using local neural TTS
- Controls a real, visible browser (YouTube search & playback)

### What Scrapbot.ai Does NOT Do (yet)

- Smart-home integrations
- Mobile app / LAN server
- Custom-trained wake word
- Multi-turn memory beyond a session

For current changes and roadmap, see [CHANGELOG.md](./CHANGELOG.md).

---

## Voice Processing Pipeline

Continuous listening (local)
↓
Wake word detection (local)
↓
Silence detection (local)
↓
Speech-to-Text (cloud)
↓
Intent reasoning (cloud LLM)
↓
Structured JSON response
↓
Local action execution
↓
Text-to-Speech (local)

## Browser Automation

Scrapbot uses **Playwright (Chromium)** in **non-headless mode** to control a real browser window.

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
├── tests/
├── .env
├── .env.demo
├── listener.py
├── main.py
├── browser.py
├── app_state.py
├── Makefile
├── README.md
├── reasoner.py
└── requirements.txt

### Key Files

- `listener.py` — audio capture, wake-word detection, silence detection
- `reasoner.py` — STT handling, intent reasoning, JSON responses
- `browser.py` — Playwright browser control
- `app_state.py` — shared async application state
- `main.py` — event loop and orchestration
- `Makefile` — environment setup and execution

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
- Google Gemini (intent reasoning)
- Structured JSON intent contracts

### Voice Output
- Local TTS (CPU-based)

### Browser Automation
- Playwright
- Chromium (bundled, non-headless)

### Platform
- Linux (Debian / Ubuntu)
- **No Docker required**

---

## Configuration

Configuration is explicit and file-based:

- `.env` — credentials and runtime settings (not committed)
- `.env.demo` — template for required variables
- `config.py` — runtime constants and defaults

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

- Audible wake-word confirmation sound
- Confidence-based clarification prompts
- Expanded intent library
- Multi-command sessions
- Custom wake-word training
- Streaming STT for lower latency

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
# Ok House

**Ok House** is a local-first, Linux-based voice assistant focused on **continuous listening**, **wake word detection**, **speech understanding**, and **voice feedback**, designed to run entirely on an old laptop or low-resource machine.

The project is intentionally minimal and modular, with a strong emphasis on **real-time audio processing**, **AI-driven intent recognition**, and **developer ownership**.

---

### Usage
make help

make install

make run

make clean

---

## What Ok House Does

- Continuously listens to microphone input
- Detects a custom wake word ("hey mycroft")
- Records speech and waits for silence
- Converts speech to text (STT)
- Infers user intent from a predefined intent list
- Produces structured JSON responses
- Replies to the user using local neural text-to-speech (TTS)

All core logic is designed to be **local-first** and runnable on commodity hardware.

---

## What Ok House Does NOT Do (yet)

- ❌ Browser automation
- ❌ Custom Ok House wakeword
- ❌ Smart-home integrations
- ❌ Mobile app
- ❌ Always-on cloud dependency
- ❌ Consumer assistant UI

Ok House is a **voice processing and intent inference engine**, not a full Alexa replacement.

---

## Voice Processing Pipeline

```
→ Continuous listening (local) 

→ Wake word detection (local) 

→ Silence detection (local) 

→ Speech-to-Text (STT) (cloud) 

→ Intent recognition (cloud) 

→ JSON response 

→ Text-to-Speech (TTS) (local)
```

---

## Tech Stack

### Audio & Runtime
- **Python 3.10+**
- **AsyncIO**
- **PyAudio** (real-time microphone streaming)
- **WebRTC VAD** (silence detection)

### AI / NLP
- **Sentence Transformers** — wake word & semantic intent matching
- **Google Speech-to-Text** — speech recognition
- **Google Dialogflow** — intent classification and NLP

### Voice Output
- **Coqui TTS** — local neural text-to-speech (CPU-based)

### System
- **Linux (Debian / Ubuntu)**
- **Local-first, event-driven architecture**
- **Conternarized ready to run project**

---

## Example Flow

1. System continuously listens to audio input
2. User says:
   
   **"hey mycroft, what time is it"**

3. Wake word is detected via embeddings
4. Speech is recorded until silence is detected
5. Audio is transcribed to text
6. Intent is inferred and returned as structured JSON
7. A spoken response is generated via TTS

---

## Hardware Requirements

- Any Linux laptop or PC
- x86_64 CPU
- 4–8 GB RAM recommended
- Microphone
- Speakers or headphones
---

## Project Status

⚠️ Early-stage / experimental

- Core pipeline defined
- APIs and interfaces may evolve

⚠️ todo
- Browser control

---

## Philosophy

- **Local-first** — you own the system
- **Explicit over magical** — transparent processing
- **Minimal dependencies** — fewer moving parts
- **Composable** — easy to extend with new intents

---

## License

You are welcome to fork this project. Vibe coded with free chatgpt version GPT-5.2.
MIT License

---

## Audience

- Backend engineers
- Applied AI / NLP engineers
- Linux users
- Developers interested in real-time audio systems

If you want a consumer assistant, buy one.
If you want to understand and control the pipeline, deploy Ok House
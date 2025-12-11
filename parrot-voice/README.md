
# Parrot Voice Wake

Offline voice wake-word detection for Linux (Ubuntu / Debian).  
Say **“parrot”** to wake your local automation, media control, or agent.

✅ Fully offline  
✅ No API keys  
✅ Simple setup  
✅ Designed for desktop Linux  

---

## Features

- Wake-word detection using **Vosk**
- Privacy-friendly (runs 100% locally)
- Low CPU usage
- Easy to extend (media players, DBus, FastAPI, shell commands)
- Configurable wake word (default: **parrot**)

---

## Requirements

- Linux (Ubuntu / Debian tested)
- Python **3.9+**
- Working microphone

System packages:
```bash
sudo apt update
sudo apt install -y python3-pip portaudio19-dev
```

---

## Installation

### 1. Create and activate a virtual environment (recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

---

## Python Dependencies

Create `requirements.txt` in the project root (already included in repo):

```txt
vosk
sounddevice
```

---

## Download Speech Model (Required)

Vosk requires an offline speech model.

```bash
mkdir -p ~/.vosk
cd ~/.vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

---

## Project Layout

```
parrot-voice/
├── README.md
├── requirements.txt
├── pyproject.toml
│
├── parrot_voice/
│   ├── __init__.py
│   └── wake.py
│
└── scripts/
    └── parrot-wake
```

---

## Wake-Word Listener Script

File: `parrot_voice/wake.py`

```python
import queue
import sounddevice as sd
import json
import sys
import time
import os
from vosk import Model, KaldiRecognizer

MODEL_PATH = os.path.expanduser("~/.vosk/vosk-model-small-en-us-0.15")
WAKE_WORD = "parrot"
SAMPLE_RATE = 16000

q = queue.Queue()
last_wake = 0

def audio_callback(indata, frames, time_, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def on_wake():
    global last_wake
    now = time.time()
    if now - last_wake < 2:
        return
    last_wake = now
    print("\n🦜 PARROT AWAKE\n")

    # Add your automation here
    # os.system("playerctl play-pause")
    # os.system("notify-send 'Parrot' 'Listening...'")

def main():
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback,
    ):
        print("🎙️ Listening... say 'parrot'")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get("text", "")
                if WAKE_WORD in text.lower():
                    on_wake()
            else:
                partial = json.loads(rec.PartialResult()).get("partial", "")
                if WAKE_WORD in partial.lower():
                    on_wake()

if __name__ == "__main__":
    main()
```

---

## Run the Listener

### Directly
```bash
python3 parrot_voice/wake.py
```

Expected output:
```
🎙️ Listening... say 'parrot'
```

Say **“parrot”** → wake event fires.

---

## Optional CLI Script

File: `scripts/parrot-wake`

```bash
#!/usr/bin/env bash
source "$(dirname "$0")/../.venv/bin/activate"
python3 "$(dirname "$0")/../parrot_voice/wake.py"
```

Make executable:
```bash
chmod +x scripts/parrot-wake
```

Run:
```bash
./scripts/parrot-wake
```

---

## Optional Packaging (CLI Command)

File: `pyproject.toml`

```toml
[project]
name = "parrot-voice"
version = "0.1.0"
dependencies = ["vosk", "sounddevice"]

[project.scripts]
parrot-wake = "parrot_voice.wake:main"
```

Install:
```bash
pip install .
parrot-wake
```

---

## Configuration

Edit `parrot_voice/wake.py`:

```python
WAKE_WORD = "parrot"
MODEL_PATH = "~/.vosk/vosk-model-small-en-us-0.15"
```

You can customize:
- wake word
- debounce timing
- actions triggered on wake

---

## Examples of Custom Actions

Inside `on_wake()`:
```python
os.system("playerctl play-pause")
os.system("notify-send 'Parrot' 'Listening...'")
```

---

## License

MIT

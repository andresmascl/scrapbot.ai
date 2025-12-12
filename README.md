# 🎤 Local Voice Assistant (Push-to-Talk + Cloud STT + Local Intent Execution)
**This version contains ONLY the Makefile workflow + the project filemap.**

This is the **latest simplified architecture**:

- ❌ No wake word
- ❌ No Whisper.cpp
- ❌ No VAD
- ❌ No Piper
- ✅ Push-to-talk via **keyboard shortcut**
- ✅ **Cloud STT (Google Speech-to-Text)**
- ✅ **Local intent guessing**
- ✅ **Local execution (e.g. Brave automation)**

Everything—**virtualenv, dependencies, and running**—is handled via the **Makefile**.

---

# 📁 Filemap
```bash
voicebot/
│── Makefile
│── main.py # Push-to-talk → Google STT → local intent execution
│
├── credentials/
│ └── google.json # Google service account (not committed)
│
└── venv/ # virtual environment (created by Makefile)
```


---

# 🛠 Makefile Instructions

Below is the **full Makefile-driven workflow**.  
You do **NOT** manually manage the virtual environment.

---

## ✅ 1. Setup (venv + Python dependencies)

```bash
make setup
```
This command:

Creates a Python virtual environment (venv/)

Installs required Python packages:

sounddevice

soundfile

numpy

pynput

google-cloud-speech

Verifies basic audio support

⚠️ System audio libraries (PortAudio, ALSA) must already be present on Linux.

🎤 2. Run the assistant
```bash
make run
```

Internally runs:
```bash
source venv/bin/activate && python3 main.py
```

You will see:

🟢 Ready. Hold Super + Alt + Space to speak.

Runtime behavior

Hold Super (Windows key) + Alt + Space

Speak while holding

Release keys → audio is sent to Google STT

Text is returned

Intent is guessed locally

Local action is executed

🔑 3. Google Credentials (Required)

You must provide a Google Cloud Speech-to-Text service account:

credentials/google.json


And ensure this path is used in main.py:
```bash
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials/google.json"
```

Speech-to-Text must be enabled in the Google Cloud project.

🧽 4. Clean (remove venv only)
```bash
make clean
```

Removes:

venv/


Keeps source files and credentials.

💥 5. Full reset (fresh clone state)
```bash
make distclean
```

Removes:
venv/

Any generated audio files
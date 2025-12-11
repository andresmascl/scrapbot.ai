import sounddevice as sd
import numpy as np
import queue
from whisper import transcribe_and_forward

WAKE_WORD = "parrot"
audio_q = queue.Queue()

def audio_callback(indata, frames, time, status):
    audio_q.put(indata.copy())

def listen_wake_word():
    print("🎧 Listening for wake word:", WAKE_WORD)

    sd.InputStream(callback=audio_callback, channels=1, samplerate=16000).start()

    buffer = np.zeros(16000 * 3)

    while True:
        data = audio_q.get()
        data = data.reshape(-1)
        buffer = np.concatenate([buffer[len(data):], data])

        volume = np.linalg.norm(buffer) / len(buffer)

        if volume > 0.08:
            print("🔊 Voice detected… recording")
            record_voice_command()
            break

def record_voice_command():
    import sounddevice as sd
    print("🎙 Recording audio...")
    duration = 4
    fs = 16000
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    audio_path = "last_command.wav"
    import numpy as np
    np.save(audio_path, audio)

    print("📩 Sending to Whisper…")
    transcribe_and_forward(audio_path)
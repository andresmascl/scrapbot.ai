import pyaudio
import numpy as np
import time

RATE = 44100        # match your device default
CHANNELS = 1
FRAME_SIZE = 1024
DEVICE_INDEX = None  # use default (PipeWire routes correctly)

p = pyaudio.PyAudio()

stream = p.open(
    format=pyaudio.paInt16,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAME_SIZE,
    input_device_index=DEVICE_INDEX,
)

print("🎙️ Speak into the mic (Ctrl+C to stop)")

try:
    while True:
        data = stream.read(FRAME_SIZE, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        rms = np.sqrt(np.mean(samples ** 2))
        bar = "#" * min(int(rms / 200), 50)
        print(f"\rRMS {int(rms):5d} | {bar}", end="")
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()

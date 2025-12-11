
def on_wake():
    subprocess.run([
        "python3",
        "../voice-command/voice_to_text.py"
    ])

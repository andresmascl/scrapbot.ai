## What Scrapbot.ai Does

- Continuously listens to microphone input
- Detects a custom wake word ("hey Mycroft")


## TODO:
1. Implement Speech to Text:  After Wake Word Detection, Local agent sends voice to STT service
2. Local Agent Sends Transcribed text and PROMPT.md to LLM.  Local Agent reads and prints out the full json response from LLM.
3. Play response back to the user using local text-to-speech (TTS)
4. Implement Youtube Play Browser automation
5. Implement Custom Scrapbot.ai wakeword
6. Add extra wake-word filter at LLM level
7. Mobile app to serve over LAN

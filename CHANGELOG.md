## What Scrapbot.ai Does

- Continuously listens to microphone input
- Detects a custom wake word ("hey mycroft")


## TODO:
1. After Wake Word Detection, Local Agent Sends PROMPT.md to LLM & Streams Speech Until it Stops.  We will use Multimodal Live API, for this, which is already enabled on GCP's Service Account. Local Agent reads and prints out the full json response from LLM for now to test LLM funcionality.
2. Browser automation
3. Custom Scrapbot.ai wakeword
4. Smart-home integrations
5. Mobile app to serve on local network
6. Always-on cloud dependency
8. Infers user intent from a predefined intent list
9. Produces structured JSON responses
10. Replies to the user using local neural text-to-speech (TTS)
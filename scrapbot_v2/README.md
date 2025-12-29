# Scrapbot V2 - Refactored Architecture

## Overview

This is a complete refactoring of the scrapbot application to address instability issues caused by:
- Shared global state
- Nested async generators
- Race conditions in queue operations
- Fire-and-forget background tasks
- Complex async control flow

## Key Design Principles

### 1. **Linear Session Loop**
All session logic is in ONE function (`session.py:run_session_loop`) that owns the entire lifecycle:
```
wake → record → process → speak → reset → loop
```

### 2. **No Global State**
All state is local to the session loop function:
```python
session_state = {
    'wake_allowed': True,
    'in_session': False,
    'last_wake_time': 0.0,
}
```

### 3. **No Generators**
Instead of async generators that yield chunks, functions now:
- **Return complete buffers** (e.g., `record_until_silence()` returns bytes)
- **Process inline** (wake detection happens in main loop)

### 4. **Sequential Operations**
No fire-and-forget tasks (except harmless ones like wake sound):
```python
await speak_text(feedback)         # Wait for TTS
await _drain_stream(stream, 0.5)   # Wait for drain
await asyncio.sleep(5.0)           # Wait for rearm delay
```

### 5. **Reused Functions**
Old working functions are extracted as pure utilities:
- `audio_utils.py`: Wake detection, VAD, resampling
- `llm_client.py`: STT, TTS, LLM calls

## File Structure

```
scrapbot_v2/
├── __init__.py           # Package exports
├── config.py             # Centralized configuration
├── session.py            # Main linear session loop ⭐
├── audio_utils.py        # Pure audio functions (reused)
├── llm_client.py         # API client functions (reused)
├── main.py               # Simple entry point
└── README.md             # This file
```

## Architecture Comparison

### Old Architecture (Unstable)
```
main_loop()
  ├─ listener.listen() [async generator]
  │   ├─ wake_word_worker() [background task]
  │   │   └─ Uses global_wake_allowed
  │   ├─ audio_queue [shared]
  │   └─ event_queue [shared]
  │
  └─ reasoner.process_voice_command(audio_gen)
      ├─ Consumes same generator as main_loop
      ├─ Calls listener.rearm_wake_word()
      │   └─ Creates background drain task [fire-and-forget]
      └─ Modifies listener.global_wake_allowed
```

**Problems:**
- 4 levels of nested async
- Shared generator state between main loop & reasoner
- Global `wake_allowed` flag accessed from 5+ places
- Fire-and-forget drain task could corrupt next session
- Race conditions in queue check-then-act patterns

### New Architecture (Stable)
```
run_session_loop()
  ├─ Phase 1: Wake detection (inline, no background task)
  │   └─ Local state: wake_buffer, session_state
  │
  ├─ Phase 2: Record command (inline, no generator)
  │   └─ Local state: frames, vad_buffer
  │
  ├─ Phase 3: Transcribe & Process
  │   ├─ await transcribe_audio() [reused function]
  │   └─ await get_llm_response() [reused function]
  │
  ├─ Phase 4: Speak response
  │   └─ await speak_text() [reused function]
  │
  └─ Phase 5: Drain & rearm (sequential)
      ├─ await _drain_stream()
      └─ await asyncio.sleep()
```

**Benefits:**
- 2 levels max (main → utility function)
- No shared state (all local)
- No global flags
- All operations awaited (no fire-and-forget)
- Linear control flow (easy to debug)

## Running the New Version

From the repository root:

```bash
# Using Python module syntax
python -m scrapbot_v2.main

# Or directly
python scrapbot_v2/main.py
```

## Migration Strategy

1. **Keep old code intact** - Don't modify `main.py`, `listener.py`, `reasoner.py`
2. **Test new version** - Run `scrapbot_v2` and compare behavior
3. **Gradual cutover** - Once stable, switch Docker entrypoint
4. **Remove old code** - After confidence, archive old implementation

## Testing

The new architecture makes testing easier:

```python
# Test wake detection (pure function)
score = detect_wake_word(audio_frame, "hey_mycroft", 0.7)
assert score > 0.7

# Test VAD (pure function)
prob = is_speech(audio_chunk, 0.5)
assert prob > 0.5

# Test transcription (async but isolated)
transcript = await transcribe_audio(client, audio_bytes)
assert len(transcript) > 0
```

## Known Limitations

1. **Still uses PyAudio** - Same audio backend (could swap with sounddevice later)
2. **ALSA errors suppressed** - Inherits error suppression from old code
3. **No action execution yet** - Only processes voice commands, doesn't execute actions

## Future Improvements

- [ ] Add proper logging (replace print statements)
- [ ] Add metrics/telemetry (session duration, error rates)
- [ ] Add state machine visualization
- [ ] Add comprehensive tests
- [ ] Replace PyAudio with sounddevice
- [ ] Add action execution logic
- [ ] Add configuration validation

## Troubleshooting

### Wake word not detected
- Check `WAKE_THRESHOLD` in config (default: 0.7)
- Enable volume bar: `ENABLE_VOLUME_BAR=1`
- Check wake model loaded correctly

### TTS feedback causes re-trigger
- Increase `TTS_REARM_DELAY_SEC` (default: 5.0)
- Check `STREAM_DRAIN_SEC` (default: 0.5)

### Transcription fails
- Verify `GOOGLE_API_KEY` or `GCP_PROJECT_ID`
- Check model name: `VERTEX_MODEL_NAME`
- Test network connectivity

## Contact

For questions about the refactoring strategy, refer to the initial design discussion.

# AI Assistant Instructions for Scrap AI Bot

## Purpose of This Document

This document is specifically written for AI coding assistants (like Claude, GitHub Copilot, Cursor, etc.) working on the Scrap AI Bot codebase. It provides context, conventions, and guidelines to help AI assistants make appropriate code contributions.

---

## Project Context

### What This Project Does

Scrap AI Bot adds voice control to Anthropic's Computer Use Demo. The system:

1. Listens for wake word "Ok Computer"
2. Captures audio after wake word
3. Transcribes audio to text (Whisper)
4. Sends text + screenshot to Claude
5. Claude reasons about actions and controls computer
6. Executes mouse/keyboard/bash commands
7. Returns to listening

### Key Architecture Layers

```
Voice Layer (YOU WILL WORK HERE MOSTLY)
├── Wake word detection (Porcupine)
├── Audio capture (PyAudio)
├── Transcription (Whisper API)
└── Orchestration (connects to Computer Use)

Computer Use Layer (RARELY MODIFY)
├── Screenshot capture
├── Claude API integration
├── Tool execution
└── (This is Anthropic's code as submodule)

System Layer (DON'T MODIFY)
└── Docker, X11, VNC
```

**Important**: You will primarily work in the `voice-layer/` directory. The `computer-use-demo/` is a git submodule - only modify if absolutely necessary and document why.

---

## Code Style and Conventions

### Python Standards

```python
# ALWAYS use type hints
from typing import Optional, Dict, Any, Callable

async def process_audio(
    audio_data: bytes,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process captured audio data.
    
    Args:
        audio_data: Raw audio bytes from microphone
        config: Optional configuration overrides
        
    Returns:
        Dictionary with 'text' and 'confidence' keys
        
    Raises:
        TranscriptionError: If Whisper API fails
    """
    pass

# ALWAYS use async/await for I/O operations
async def call_api():
    response = await client.post(...)  # Good
    
# DON'T use blocking calls in async functions
def blocking_call():
    response = requests.post(...)  # Bad in async context
```

### Naming Conventions

```python
# Classes: PascalCase
class AudioCapture:
    pass

# Functions/methods: snake_case
def capture_audio():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RECORDING_DURATION = 10

# Private methods: _leading_underscore
def _internal_helper():
    pass

# Config keys: lowercase with underscores
config = {
    "sample_rate": 16000,
    "wake_word_sensitivity": 0.5
}
```

### File Organization

```python
# Standard import order:
# 1. Standard library
import os
import logging
from typing import Optional

# 2. Third-party packages
import pyaudio
import anthropic

# 3. Local imports
from voice_layer.utils import logger
from voice_layer.config import load_config
```

---

## Critical Implementation Details

### 1. Audio Handling

**ALWAYS** use these audio specifications:
```python
SAMPLE_RATE = 16000  # Whisper-optimized
CHANNELS = 1  # Mono
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16  # 16-bit
```

**NEVER** use different sample rates or formats without updating config.

### 2. API Error Handling

**ALWAYS** implement retry logic for API calls:
```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_whisper_api(audio_file: str) -> dict:
    """Calls Whisper with automatic retry."""
    try:
        response = await client.transcribe(audio_file)
        return response
    except Exception as e:
        logger.error(f"Whisper API error: {e}")
        raise
```

**NEVER** let API failures crash the entire system - always catch and log.

### 3. State Management

The orchestrator maintains state. **ALWAYS** update state atomically:

```python
# GOOD: Atomic state update
async def update_state(self, new_state: State):
    async with self._state_lock:
        self._state = new_state
        await self._notify_observers()

# BAD: Race condition possible
def update_state(self, new_state: State):
    self._state = new_state  # Not thread-safe
```

### 4. Resource Cleanup

**ALWAYS** clean up resources in finally blocks:

```python
# GOOD
audio_stream = None
try:
    audio_stream = pyaudio.PyAudio().open(...)
    data = audio_stream.read(CHUNK_SIZE)
finally:
    if audio_stream:
        audio_stream.stop_stream()
        audio_stream.close()

# BETTER: Use context managers
async with AudioStream() as stream:
    data = await stream.read()
```

---

## Integration Points

### How Voice Layer Connects to Computer Use

```python
# voice-layer/computer_use_client.py

class ComputerUseClient:
    """Interface to Anthropic's Computer Use Demo"""
    
    async def execute_command(self, command: str) -> dict:
        """
        Send voice command to Computer Use sampling loop.
        
        This calls the modified sampling_loop function in
        computer-use-demo/computer_use_demo/loop.py
        
        DO NOT modify the sampling loop directly unless necessary.
        Instead, inject commands through the API parameter.
        """
        # Implementation here
```

**Key principle**: Voice layer is a CLIENT of Computer Use, not part of it.

### Configuration Loading

```python
# ALWAYS load config from yaml
from voice_layer.utils.config import load_config

config = load_config("config/settings.yaml")
wake_word_sensitivity = config["wake_word"]["sensitivity"]

# NEVER hardcode config values
sensitivity = 0.5  # Bad - should be in config
```

### Logging

```python
# ALWAYS use structured logging
from voice_layer.utils.logger import get_logger

logger = get_logger(__name__)

# GOOD: Structured with context
logger.info(
    "Wake word detected",
    extra={
        "keyword": "ok computer",
        "confidence": 0.95,
        "timestamp": time.time()
    }
)

# BAD: Unstructured
logger.info("Wake word detected")
print("Something happened")  # Never use print()
```

---

## Common Tasks and Patterns

### Task 1: Adding a New Audio Processing Step

```python
# 1. Create new file in voice-layer/
# voice-layer/audio_processing.py

from typing import bytes

async def process_audio(audio_data: bytes) -> bytes:
    """
    Process raw audio data.
    
    Args:
        audio_data: Raw audio from microphone
        
    Returns:
        Processed audio data
    """
    # Implementation
    return processed_data

# 2. Add to orchestrator
# voice-layer/orchestrator.py

from voice_layer.audio_processing import process_audio

class VoiceOrchestrator:
    async def _handle_audio(self, raw_audio: bytes):
        processed = await process_audio(raw_audio)
        transcript = await self.transcriber.transcribe(processed)
        # ...

# 3. Add tests
# tests/unit/test_audio_processing.py

import pytest
from voice_layer.audio_processing import process_audio

@pytest.mark.asyncio
async def test_process_audio():
    raw_audio = b"..."  # Test data
    result = await process_audio(raw_audio)
    assert len(result) > 0

# 4. Update config if needed
# config/settings.yaml

audio_processing:
  filter_enabled: true
  noise_reduction: 0.5
```

### Task 2: Modifying Wake Word Behavior

```python
# voice-layer/wake_word.py

class WakeWordDetector:
    def __init__(self, config: dict):
        # ALWAYS support config override
        self.sensitivity = config.get("sensitivity", 0.5)
        self.keyword = config.get("keyword", "ok computer")
        
    async def detect(self) -> bool:
        """
        Detect wake word in audio stream.
        
        Returns:
            True if wake word detected, False otherwise
        """
        # If modifying detection logic:
        # 1. Keep backward compatibility
        # 2. Add feature flags in config
        # 3. Log detection events
        # 4. Update tests
```

### Task 3: Adding API Integration

```python
# voice-layer/api_client.py

from typing import Optional
import httpx

class APIClient:
    def __init__(self, base_url: str, api_key: str):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0
        )
    
    @retry(stop_after_attempt(3))
    async def call_api(
        self,
        endpoint: str,
        data: dict
    ) -> dict:
        """
        Call external API with automatic retry.
        
        ALWAYS:
        - Use async httpx client
        - Add retry decorator
        - Set reasonable timeout
        - Log requests and responses
        - Handle errors gracefully
        """
        try:
            response = await self._client.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API call failed: {e}")
            raise
    
    async def close(self):
        """ALWAYS provide cleanup method"""
        await self._client.aclose()
```

---

## Testing Guidelines

### What to Test

```python
# ALWAYS test:
# 1. Happy path
@pytest.mark.asyncio
async def test_audio_capture_success():
    capturer = AudioCapture()
    audio = await capturer.capture(duration=1)
    assert len(audio) > 0

# 2. Error cases
@pytest.mark.asyncio
async def test_audio_capture_no_device():
    capturer = AudioCapture(device_index=999)
    with pytest.raises(AudioDeviceError):
        await capturer.capture()

# 3. Edge cases
@pytest.mark.asyncio
async def test_audio_capture_zero_duration():
    capturer = AudioCapture()
    audio = await capturer.capture(duration=0)
    assert audio == b""

# 4. Integration points
@pytest.mark.asyncio
async def test_orchestrator_full_flow(mock_apis):
    orchestrator = VoiceOrchestrator()
    # Mock external APIs
    result = await orchestrator.process_command("test command")
    assert result["status"] == "success"
```

### Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_wake_word.py
│   ├── test_audio_capture.py
│   └── test_transcription.py
├── integration/             # Tests with real APIs
│   ├── test_whisper_api.py
│   └── test_claude_api.py
└── e2e/                     # Full system tests
    └── test_voice_command_flow.py
```

---

## Common Pitfalls to Avoid

### ❌ DON'T: Modify computer-use-demo submodule directly

```python
# BAD: Editing files in computer-use-demo/
# This will be overwritten on submodule update
```

**DO**: Create wrapper/adapter in voice-layer

```python
# GOOD: Wrapping functionality
from voice_layer.computer_use_client import ComputerUseClient
```

### ❌ DON'T: Use blocking I/O in async functions

```python
# BAD
async def get_transcript():
    response = requests.post(...)  # Blocks event loop
    return response.json()
```

**DO**: Use async libraries

```python
# GOOD
async def get_transcript():
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
        return response.json()
```

### ❌ DON'T: Hardcode file paths

```python
# BAD
audio_file = "/home/user/audio.wav"
```

**DO**: Use Path and config

```python
# GOOD
from pathlib import Path
audio_dir = Path(config["paths"]["audio_dir"])
audio_file = audio_dir / "recording.wav"
```

### ❌ DON'T: Ignore resource limits

```python
# BAD: Can accumulate indefinitely
recordings = []
while True:
    recordings.append(capture_audio())  # Memory leak
```

**DO**: Implement cleanup

```python
# GOOD: Limited buffer with cleanup
from collections import deque
recordings = deque(maxlen=10)  # Only keep last 10
```

---

## Debug and Troubleshooting

### Logging Levels

```python
# Use appropriate log levels:

logger.debug("Audio frame: size=%d", len(frame))
# Development only, verbose details

logger.info("Wake word detected: keyword='%s'", keyword)
# Normal operation events

logger.warning("Low confidence: %.2f < threshold %.2f", conf, threshold)
# Unexpected but handled situations

logger.error("API call failed: %s", error, exc_info=True)
# Errors that prevent operation

logger.critical("Cannot access microphone device")
# System-level failures
```

### Common Debug Scenarios

**Wake word not detecting:**
```python
# Add debug logging
logger.debug(
    "Audio frame processed",
    extra={
        "frame_size": len(audio_frame),
        "keyword_index": keyword_index,
        "sensitivity": self.sensitivity
    }
)

# Test with different sensitivity
python -m voice_layer.wake_word --test --sensitivity 0.8
```

**Transcription failing:**
```python
# Log audio file details
import wave
with wave.open(audio_file, 'rb') as f:
    logger.debug(
        "Audio file details",
        extra={
            "sample_rate": f.getframerate(),
            "channels": f.getnchannels(),
            "duration": f.getnframes() / f.getframerate()
        }
    )
```

---

## When to Ask for Human Review

Request human review when:

1. **Modifying core architecture** - Changes to orchestrator state machine
2. **Adding new dependencies** - New packages in requirements.txt
3. **Changing API contracts** - Function signatures in public APIs
4. **Security implications** - API key handling, user data processing
5. **Breaking changes** - Anything that changes existing behavior
6. **Submodule modifications** - Changes to computer-use-demo/
7. **Docker configuration** - Dockerfile or docker-compose changes

## Questions to Ask Yourself

Before implementing a feature:

- [ ] Does this belong in voice-layer or computer-use-demo?
- [ ] Is there a config value that should control this?
- [ ] What happens if an API call fails?
- [ ] Have I added appropriate logging?
- [ ] Are resources cleaned up properly?
- [ ] Does this need tests?
- [ ] Will this work in Docker container?
- [ ] Is this async-safe if in async context?

---

## Example: Complete Feature Implementation

**Task**: Add confidence threshold filtering for transcriptions

```python
# 1. Add config
# config/settings.yaml
transcription:
  min_confidence: 0.7
  retry_on_low_confidence: true
  max_retries: 2

# 2. Update transcriber
# voice-layer/transcription.py
class Transcriber:
    def __init__(self, config: dict):
        self.min_confidence = config.get("min_confidence", 0.7)
        self.retry_enabled = config.get("retry_on_low_confidence", True)
        self.max_retries = config.get("max_retries", 2)
    
    async def transcribe(self, audio_file: str) -> Optional[dict]:
        """Transcribe with confidence filtering."""
        for attempt in range(self.max_retries + 1):
            result = await self._call_whisper_api(audio_file)
            
            if result["confidence"] >= self.min_confidence:
                logger.info(
                    "Transcription successful",
                    extra={
                        "confidence": result["confidence"],
                        "attempt": attempt + 1
                    }
                )
                return result
            
            if not self.retry_enabled or attempt == self.max_retries:
                logger.warning(
                    "Low confidence transcription",
                    extra={
                        "confidence": result["confidence"],
                        "threshold": self.min_confidence,
                        "attempts": attempt + 1
                    }
                )
                return None
            
            logger.debug(f"Retrying transcription (attempt {attempt + 2})")
            await asyncio.sleep(1)
        
        return None

# 3. Update orchestrator
# voice-layer/orchestrator.py
async def _process_audio(self, audio: bytes):
    transcript = await self.transcriber.transcribe(audio_file)
    
    if transcript is None:
        logger.warning("Transcription confidence too low, ignoring")
        await self._play_error_sound()  # Optional
        return
    
    await self.computer_use_client.execute_command(transcript["text"])

# 4. Add tests
# tests/unit/test_transcription.py
@pytest.mark.asyncio
async def test_low_confidence_filtered():
    config = {"min_confidence": 0.8}
    transcriber = Transcriber(config)
    
    # Mock API to return low confidence
    with patch.object(transcriber, "_call_whisper_api") as mock:
        mock.return_value = {"text": "hello", "confidence": 0.5}
        result = await transcriber.transcribe("test.wav")
        assert result is None

@pytest.mark.asyncio
async def test_retry_on_low_confidence():
    config = {
        "min_confidence": 0.8,
        "retry_on_low_confidence": True,
        "max_retries": 2
    }
    transcriber = Transcriber(config)
    
    with patch.object(transcriber, "_call_whisper_api") as mock:
        # First call low confidence, second call high
        mock.side_effect = [
            {"text": "hello", "confidence": 0.5},
            {"text": "hello", "confidence": 0.9}
        ]
        result = await transcriber.transcribe("test.wav")
        assert result["confidence"] == 0.9
        assert mock.call_count == 2

# 5. Update documentation
# Update ARCHITECTURE.md with new config options
# Update README.md with behavior explanation
```

---

## Quick Reference

### File Structure at a Glance

```
voice-layer/
├── __init__.py
├── wake_word.py          # Wake word detection
├── audio_capture.py      # Audio recording
├── transcription.py      # Speech-to-text
├── computer_use_client.py # Interface to Computer Use
├── orchestrator.py       # Main coordination
└── utils/
    ├── logger.py         # Logging setup
    ├── config.py         # Config loading
    └── errors.py         # Custom exceptions
```

### Key Classes

- `WakeWordDetector` - Listens for "Ok Computer"
- `AudioCapture` - Records audio
- `Transcriber` - Converts speech to text
- `ComputerUseClient` - Sends commands to Claude
- `VoiceOrchestrator` - Coordinates everything

### Key Config Sections

```yaml
wake_word:      # Porcupine settings
audio:          # PyAudio settings
transcription:  # Whisper settings
computer_use:   # Claude settings
logging:        # Log levels and files
```

---

## Final Reminders

1. **Privacy First**: Only send necessary data to cloud
2. **Fail Gracefully**: Never crash, always log and recover
3. **Test Everything**: Unit, integration, and e2e tests
4. **Document Changes**: Update relevant .md files
5. **Ask When Unsure**: Request human review for big changes

**You're building voice control for an AI that controls a computer. Make it robust, secure, and maintainable.**

---

**Document Version**: 1.0  
**Last Updated**: December 2025  
**For AI Assistants**: Claude, Copilot, Cursor, and friends

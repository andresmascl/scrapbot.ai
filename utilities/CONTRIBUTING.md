# Contributing to Scrap AI Bot

Thank you for your interest in contributing to Scrap AI Bot! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, constructive, and professional in all interactions. We're building something cool together.

## Ways to Contribute

- 🐛 **Bug Reports** - Found a bug? Open an issue
- 💡 **Feature Requests** - Have an idea? Start a discussion
- 📝 **Documentation** - Improve docs, add examples
- 🔧 **Code** - Fix bugs, add features, improve performance
- 🧪 **Testing** - Write tests, improve coverage
- 🎨 **Design** - UI/UX improvements

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/scrap-ai-bot.git
cd scrap-ai-bot
git remote add upstream https://github.com/andresmascl/scrap-ai-bot.git
```

### 2. Set Up Development Environment

```bash
# Initialize submodules
git submodule update --init --recursive

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy env file
cp .env.example .env
# Add your API keys to .env
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-number-description
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=voice_layer --cov-report=html

# Run specific test file
pytest tests/unit/test_wake_word.py

# Run integration tests (requires API keys)
pytest tests/integration/

# Run with verbose output
pytest -v
```

### Code Style

We use:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking
- **isort** for import sorting

```bash
# Format code
black voice-layer/

# Check linting
flake8 voice-layer/

# Check types
mypy voice-layer/

# Sort imports
isort voice-layer/

# Run all checks
./scripts/check-code.sh
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Making Changes

### 1. Write Code

- Follow the style guide in [AI_INSTRUCTIONS.md](AI_INSTRUCTIONS.md)
- Add type hints to all functions
- Write docstrings for public APIs
- Keep functions focused and small

### 2. Write Tests

- Add tests for new features
- Maintain or improve test coverage
- Test both happy path and error cases

### 3. Update Documentation

- Update README.md if user-facing changes
- Update ARCHITECTURE.md if architectural changes
- Add inline comments for complex logic
- Update CHANGELOG.md

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add TTS feedback for command confirmation"

# Follow conventional commits:
# feat: new feature
# fix: bug fix
# docs: documentation changes
# test: adding tests
# refactor: code refactoring
# perf: performance improvements
# chore: maintenance tasks
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# - Describe what changed and why
# - Reference any related issues
# - Add screenshots/videos if UI changes
```

## Pull Request Guidelines

### PR Title

Use conventional commits format:
```
feat: add confidence threshold filtering
fix: resolve wake word detection on USB mics
docs: update API integration section
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Added new tests
- [ ] All tests pass
- [ ] Tested manually

## Related Issues
Closes #123

## Screenshots (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

1. Automated checks must pass (tests, linting)
2. At least one maintainer approval required
3. Address review comments
4. Keep PR scope focused
5. Squash commits if requested

## Project Structure

```
scrap-ai-bot/
├── voice-layer/          # Your code goes here
│   ├── wake_word.py
│   ├── audio_capture.py
│   ├── transcription.py
│   └── ...
├── tests/                # Tests mirror voice-layer/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config/               # Configuration files
├── docker/               # Docker configuration
└── scripts/              # Helper scripts
```

**Important**: Don't modify `computer-use-demo/` unless absolutely necessary. It's a submodule.

## Areas Needing Help

### High Priority
- [ ] Error recovery and resilience
- [ ] Performance optimization
- [ ] Better logging and observability
- [ ] Integration tests

### Medium Priority
- [ ] TTS feedback implementation
- [ ] Task template system
- [ ] Multi-language support
- [ ] Documentation improvements

### Low Priority
- [ ] UI improvements
- [ ] Additional wake words
- [ ] Mobile control
- [ ] Plugin system

## Coding Standards

### Python

```python
# Good example
from typing import Optional

async def process_audio(
    audio_data: bytes,
    config: Optional[dict] = None
) -> dict:
    """
    Process audio data with optional config.
    
    Args:
        audio_data: Raw audio bytes
        config: Optional configuration overrides
        
    Returns:
        Processing result dictionary
        
    Raises:
        ProcessingError: If processing fails
    """
    # Implementation
    pass
```

### Documentation

```python
class AudioCapture:
    """
    Handles audio capture from microphone.
    
    This class manages PyAudio streams and provides
    methods for recording audio with configurable
    duration and silence detection.
    
    Example:
        >>> capturer = AudioCapture()
        >>> audio = await capturer.capture(duration=5)
        >>> await capturer.close()
    """
```

### Error Handling

```python
# Always use specific exceptions
try:
    result = await api_call()
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    raise

# Always clean up resources
try:
    stream = open_audio_stream()
    process_stream(stream)
finally:
    stream.close()
```

## Testing Guidelines

### Unit Tests

```python
import pytest
from voice_layer.audio_capture import AudioCapture

@pytest.mark.asyncio
async def test_audio_capture_creates_valid_data():
    """Test that audio capture returns valid data."""
    capturer = AudioCapture()
    audio = await capturer.capture(duration=1)
    
    assert isinstance(audio, bytes)
    assert len(audio) > 0
    
    await capturer.close()
```

### Integration Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_voice_pipeline(mock_apis):
    """Test complete voice command flow."""
    orchestrator = VoiceOrchestrator()
    
    # This requires API keys in environment
    result = await orchestrator.process_voice_command("test")
    
    assert result["status"] == "success"
```

### Test Coverage

Aim for:
- **Unit tests**: >80% coverage
- **Integration tests**: Key workflows
- **E2E tests**: Critical user journeys

## Documentation

### Code Comments

```python
# Use comments to explain WHY, not WHAT
# Good:
# Retry with exponential backoff to handle transient API errors
await retry_with_backoff()

# Bad:
# Call retry function
await retry_with_backoff()
```

### Docstrings

All public functions and classes need docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    One-line summary of what function does.
    
    More detailed explanation if needed. Can span
    multiple lines and explain behavior.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is empty
        APIError: When API call fails
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
```

## Debugging Tips

### Enable Debug Logging

```bash
# Set log level in config
logging:
  level: DEBUG

# Or via environment
export LOG_LEVEL=DEBUG
python -m voice_layer.orchestrator
```

### Test Individual Components

```bash
# Test wake word detection
python -m voice_layer.wake_word --test

# Test audio capture
python -m voice_layer.audio_capture --test

# Test transcription
python -m voice_layer.transcription --test --audio-file test.wav
```

### Docker Debugging

```bash
# Build with verbose output
docker build --progress=plain -t scrap-ai-bot .

# Run with interactive shell
docker run -it --entrypoint /bin/bash scrap-ai-bot

# Check logs
docker logs -f scrap-ai-bot
```

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. GitHub Actions builds and publishes release

## Getting Help

- 💬 **Discussions**: Ask questions, share ideas
- 🐛 **Issues**: Report bugs, request features
- 📧 **Email**: support@scrap-ai-bot.dev
- 📖 **Docs**: Check [ARCHITECTURE.md](ARCHITECTURE.md)

## Recognition

Contributors are recognized in:
- README.md contributors section
- CHANGELOG.md for each release
- GitHub contributors page

Thank you for contributing! 🎉

---

**Questions?** Open a discussion or contact the maintainers.

**First time contributing?** Look for issues labeled `good-first-issue`.

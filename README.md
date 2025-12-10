# Scrap AI Bot

Voice-controlled computer automation using Claude's Computer Use API. Control your computer naturally through voice commands powered by AI vision and reasoning.

![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Status](https://img.shields.io/badge/status-alpha-orange.svg)

## What is Scrap AI Bot?

Scrap AI Bot adds voice control to [Anthropic's Computer Use Demo](https://github.com/anthropics/claude-quickstarts/tree/main/computer-use-demo), enabling hands-free computer automation through natural language.

**Say "Ok Computer"** → Speak your command → Watch AI execute it

### Example Commands

- "Ok Computer, open Firefox and search for Python tutorials"
- "Ok Computer, create a new text document with today's date"
- "Ok Computer, take a screenshot and save it to desktop"
- "Ok Computer, organize my downloads folder by file type"

## How It Works

```
[Wake Word: "Ok Computer"]
    ↓
[Audio Capture]
    ↓
[Speech-to-Text (Whisper)]
    ↓
[Claude Computer Use API]
    ├── Takes screenshots
    ├── Reasons about actions
    ├── Controls mouse/keyboard
    └── Executes multi-step tasks
    ↓
[Task Complete]
```

## Features

- 🎤 **Wake word activation** - "Ok Computer" triggers listening
- 🗣️ **Natural language** - Speak commands like you would to a person
- 👁️ **Visual understanding** - Claude sees your screen and reasons about it
- 🖱️ **Full computer control** - Mouse, keyboard, and bash commands
- 🔄 **Multi-step execution** - Handles complex tasks automatically
- 🐳 **Dockerized** - Runs in safe, isolated environment
- 🔒 **Privacy-focused** - Only audio after wake word is processed

## Quick Start

### Prerequisites

- Ubuntu 20.04+ or Debian 11+ (64-bit)
- Docker and Docker Compose
- Microphone
- Display
- API Keys:
  - [Anthropic API key](https://console.anthropic.com/) (Claude)
  - [OpenAI API key](https://platform.openai.com/) (Whisper)
  - [Picovoice Access Key](https://console.picovoice.ai/) (Wake word)

### Installation

```bash
# Clone the repository
git clone https://github.com/andresmascl/scrap-ai-bot.git
cd scrap-ai-bot

# Initialize submodules (pulls Anthropic's Computer Use Demo)
git submodule update --init --recursive

# Configure API keys
cp .env.example .env
nano .env  # Add your API keys

# Build and run
./install.sh
```

### First Run

```bash
# Start the service
./start.sh

# Access the interface
# VNC viewer: localhost:5900
# Web interface: http://localhost:6080
```

Say **"Ok Computer"** followed by your command. The system will:
1. Capture your voice
2. Transcribe to text
3. Send to Claude with screenshot
4. Execute actions visually
5. Return to listening

## Project Structure

```
scrap-ai-bot/
├── README.md                       # This file
├── ARCHITECTURE.md                 # Technical architecture
├── AI_INSTRUCTIONS.md              # Instructions for AI assistants
├── CONTRIBUTING.md                 # Contribution guidelines
├── LICENSE                         # AGPL-3.0 license
├── .env.example                    # Environment variables template
│
├── computer-use-demo/              # Anthropic's demo (submodule)
│   └── [Anthropic's Computer Use implementation]
│
├── voice-layer/                    # Voice control additions
│   ├── __init__.py
│   ├── wake_word.py               # Porcupine wake word detection
│   ├── audio_capture.py           # Audio recording
│   ├── transcription.py           # Whisper API integration
│   ├── orchestrator.py            # Main coordination loop
│   └── utils/
│       ├── logger.py
│       └── config.py
│
├── config/
│   ├── settings.yaml              # Configuration
│   └── wake_word.ppn              # Wake word model
│
├── docker/
│   ├── Dockerfile.voice           # Extended Dockerfile
│   └── docker-compose.yml         # Complete stack
│
├── scripts/
│   ├── install.sh                 # Installation script
│   ├── start.sh                   # Start services
│   ├── stop.sh                    # Stop services
│   └── test_voice.sh              # Test voice pipeline
│
└── tests/
    ├── test_wake_word.py
    ├── test_audio.py
    └── test_integration.py
```

## Configuration

Edit `config/settings.yaml`:

```yaml
wake_word:
  keyword: "ok computer"
  sensitivity: 0.5

audio:
  sample_rate: 16000
  record_seconds: 5
  silence_threshold: 500

api:
  anthropic_model: "claude-sonnet-4-20250514"
  whisper_model: "whisper-1"

computer_use:
  display_width: 1024
  display_height: 768
  max_steps: 50
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Lint code
flake8 voice-layer/
black voice-layer/
```

### Architecture Overview

Scrap AI Bot is built on three layers:

1. **Voice Layer** (this project) - Wake word, audio capture, transcription
2. **AI Layer** (Anthropic's Computer Use) - Vision, reasoning, tool execution
3. **System Layer** (Docker + X11) - Safe execution environment

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

### For AI Assistants

If you're an AI coding assistant working on this project, please read [AI_INSTRUCTIONS.md](AI_INSTRUCTIONS.md) for specific guidance on how components interact and coding standards.

## Roadmap

### Current Status: Alpha

- [x] Basic voice control integration
- [x] Wake word detection
- [x] Computer Use API integration
- [ ] Stable multi-step execution
- [ ] Error recovery
- [ ] Audio feedback (TTS)

### Planned Features

- [ ] Custom wake word training
- [ ] Task templates and macros
- [ ] Voice feedback with TTS
- [ ] Multi-language support
- [ ] Performance optimizations
- [ ] Mobile device control
- [ ] Plugin system

### Commercial Features (Future)

- Premium recommendation engine
- Team collaboration features
- Enterprise security and compliance
- Managed hosting service
- Priority support

## Security & Privacy

- **Local wake word detection** - No audio sent to cloud until activated
- **Sandboxed execution** - Runs in isolated Docker container
- **API key security** - Keys stored in environment variables only
- **Audit logging** - All actions logged for review

⚠️ **Warning**: This gives AI control over your computer. Review all actions and use in controlled environments only.

## Known Limitations

- Requires display (headless mode not yet supported)
- English language only (currently)
- High API costs for extended use
- Occasional misinterpretation of visual elements
- Requires stable internet connection

## Troubleshooting

### Wake word not detecting

```bash
# Test microphone
arecord -l

# Adjust sensitivity in config/settings.yaml
wake_word:
  sensitivity: 0.7  # Increase for better detection
```

### Computer Use actions failing

```bash
# Check Docker container logs
docker logs scrap-ai-bot

# Verify API keys
./scripts/test_voice.sh
```

### Audio quality issues

```bash
# Test audio capture
python -m voice-layer.audio_capture --test

# Check sample rate matches your microphone
pactl list sources
```

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting PRs.

Key areas needing help:
- Error recovery and resilience
- Performance optimization
- Additional language support
- Documentation improvements

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

- ✅ Free for personal and non-commercial use
- ✅ Modifications must be open-sourced
- ✅ Network use triggers source disclosure
- 📧 Commercial licensing available - contact: andres@scrap-ai-bot.dev

See [LICENSE](LICENSE) for full text.

## Commercial Licensing

For commercial use cases that cannot comply with AGPL-3.0 (closed-source products, SaaS offerings, etc.), commercial licenses are available.

**Contact**: andres@scrap-ai-bot.dev

## Acknowledgments

Built on top of:
- [Anthropic's Computer Use Demo](https://github.com/anthropics/claude-quickstarts/tree/main/computer-use-demo)
- [Picovoice Porcupine](https://github.com/Picovoice/porcupine) for wake word detection
- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition

## Support

- 📖 [Documentation](https://github.com/andresmascl/scrap-ai-bot/wiki)
- 🐛 [Issue Tracker](https://github.com/andresmascl/scrap-ai-bot/issues)
- 💬 [Discussions](https://github.com/andresmascl/scrap-ai-bot/discussions)
- 📧 Email: support@scrap-ai-bot.dev

## Star History

If you find this project useful, please consider starring it on GitHub!

---

**Made with ❤️ by [andresmascl](https://github.com/andresmascl)**

**Status**: Alpha - Not recommended for production use

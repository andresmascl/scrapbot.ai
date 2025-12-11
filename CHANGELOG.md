# Changelog

All notable changes to Scrap AI Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- TTS feedback for command confirmation
- Task template system for complex workflows
- Multi-language support
- Custom wake word training
- Performance optimizations
- Mobile device control

## [0.1.0] - 2025-12-10

### Added
- Initial release of Scrap AI Bot
- Voice control layer on top of Anthropic's Computer Use Demo
- Wake word detection using Porcupine ("Ok Computer")
- Audio capture with PyAudio
- Speech-to-text using OpenAI Whisper API
- Integration with Claude Computer Use API
- Docker containerization for safe execution
- Complete documentation (README, ARCHITECTURE, AI_INSTRUCTIONS, CONTRIBUTING)
- Installation and management scripts (install.sh, start.sh, stop.sh)
- Configuration system with YAML and environment variables
- Logging infrastructure with structlog
- Basic error handling and retry logic
- Health checks for Docker containers
- Audio device passthrough configuration
- AGPL-3.0 license with commercial licensing option

### Known Issues
- Audio passthrough may require manual configuration on some systems
- Wake word detection sensitivity needs tuning per environment
- Limited to English language only
- Requires stable internet connection for all operations
- High API costs for extended use
- No error recovery for failed multi-step tasks

### Requirements
- Ubuntu 20.04+ or Debian 11+
- Docker and Docker Compose
- Python 3.8+
- Working microphone
- API keys: Anthropic, OpenAI, Picovoice

### Documentation
- README.md - User guide and quick start
- ARCHITECTURE.md - Technical architecture details
- AI_INSTRUCTIONS.md - Guidelines for AI coding assistants
- CONTRIBUTING.md - Contribution guidelines

### Credits
- Built on [Anthropic's Computer Use Demo](https://github.com/anthropics/claude-quickstarts/tree/main/computer-use-demo)
- Wake word detection by [Picovoice Porcupine](https://github.com/Picovoice/porcupine)
- Speech recognition by [OpenAI Whisper](https://github.com/openai/whisper)

---

## Version History

### Format
- **[Unreleased]** - Changes in development
- **[X.Y.Z]** - Released versions with date
  - **Added** - New features
  - **Changed** - Changes to existing features
  - **Deprecated** - Soon-to-be removed features
  - **Removed** - Removed features
  - **Fixed** - Bug fixes
  - **Security** - Security improvements

### Links
- [Unreleased]: https://github.com/andresmascl/scrap-ai-bot/compare/v0.1.0...HEAD
- [0.1.0]: https://github.com/andresmascl/scrap-ai-bot/releases/tag/v0.1.0

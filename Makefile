# -------------------------
# Project config
# -------------------------

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# -------------------------
# Default target
# -------------------------

.PHONY: help
help:
	@echo "Scrapbot (host-native)"
	@echo ""
	@echo "Targets:"
	@echo "  make venv        Create virtual environment"
	@echo "  make deps        Install Python dependencies"
	@echo "  make tts         Install Piper TTS and voices"
	@echo "  make run         Run Scrapbot"
	@echo "  make clean       Remove virtualenv and caches"
	@echo "  make test        Run tests"

# -------------------------
# Environment setup
# -------------------------

.PHONY: venv
venv:
	python3 -m venv $(VENV)
	sudo apt install -y ffmpeg espeak-ng


.PHONY: deps
deps: venv tts
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install silero-vad==6.2.0 --no-deps
	@echo "PYTHONPATH=. >> .env"


# -------------------------
# Run
# -------------------------

.PHONY: run
run:
	$(PYTHON) main.py

# -------------------------
# Maintenance
# -------------------------

.PHONY: clean
clean:
	sudo rm -rf $(VENV)

.PHONY: test
test:
	espeak --stdout "this will speak" | ffplay -autoexit -f wav -i pipe:0

# -------------------------
# TTS Setup
# -------------------------

.PHONY: tts
tts:
	mkdir -p piper_tts
	# Download and extract Piper (Linux x86_64)
	wget -nc -O piper.tar.gz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
	tar -xzf piper.tar.gz -C piper_tts --strip-components=1 || true
	rm -f piper.tar.gz
	# Download English Voice (Lessac Medium)
	wget -nc -P piper_tts/ https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
	wget -nc -P piper_tts/ https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
	# Download Spanish Voice (Sharvard Medium)
	wget -nc -P piper_tts/ https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx
	wget -nc -P piper_tts/ https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json
	@echo "✅ Piper TTS and voices installed in piper_tts/"
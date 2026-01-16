# -------------------------
# Project config
# -------------------------

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# -------------------------
# Default target
# -------------------------

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "Scrapbot (host-native)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# -------------------------
# Environment setup
# -------------------------

$(VENV):
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	@echo "Installing system dependencies..."
	sudo apt update && sudo apt install -y ffmpeg espeak-ng

.PHONY: venv
venv: $(VENV) ## Create virtual environment and install system dependencies

.PHONY: deps
deps: $(VENV) ## Install Python dependencies
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install silero-vad==6.2.0 --no-deps
	@touch .env
	@grep -q "PYTHONPATH=." .env 2>/dev/null || echo "PYTHONPATH=." >> .env
	@touch $(VENV)/.installed

$(VENV)/.installed: requirements.txt
	@$(MAKE) deps

# -------------------------
# TTS Setup
# -------------------------

.PHONY: tts
tts: ## Install Piper TTS and voices
	@if [ ! -f "piper_tts/piper" ]; then \
		mkdir -p piper_tts; \
		echo "Downloading and extracting Piper..."; \
		wget -nc -O piper.tar.gz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz; \
		tar -xzf piper.tar.gz -C piper_tts --strip-components=1 || true; \
		rm -f piper.tar.gz; \
	fi
	@if [ ! -f "piper_tts/en_US-lessac-medium.onnx" ]; then \
		echo "Downloading English voice..."; \
		wget -nc -P piper_tts/ https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx; \
		wget -nc -P piper_tts/ https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json; \
	fi
	@if [ ! -f "piper_tts/es_ES-sharvard-medium.onnx" ]; then \
		echo "Downloading Spanish voice..."; \
		wget -nc -P piper_tts/ https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx; \
		wget -nc -P piper_tts/ https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json; \
	fi
	@echo "✅ Piper TTS and voices are ready in piper_tts/"

# -------------------------
# Run
# -------------------------

.PHONY: run
run: $(VENV)/.installed tts ## Run Scrapbot (auto-installs dependencies)
	$(PYTHON) main.py

# -------------------------
# Maintenance
# -------------------------

.PHONY: clean
clean: ## Remove virtualenv, caches and temporary files
	@echo "Cleaning up..."
	sudo rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type f -name "*~" -delete
	find . -type f -name "*.log" -delete
	@echo "Cleaned."

.PHONY: clean-all
clean-all: clean ## Remove everything including TTS models
	rm -rf piper_tts

.PHONY: test
test: ## Run a simple TTS test
	espeak --stdout "this will speak" | ffplay -autoexit -f wav -i pipe:0

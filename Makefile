# -------------------------
# Project config
# -------------------------

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PLAYWRIGHT := $(VENV)/bin/playwright

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
	@echo "  make run         Run Scrapbot"
	@echo "  make clean       Remove virtualenv and caches"
	@ECHO "  make test        Run tests"

# -------------------------
# Environment setup
# -------------------------

.PHONY: venv
venv:
	python3 -m venv $(VENV)
	sudo apt install -y ffmpeg espeak-ng


.PHONY: deps
deps: venv
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install silero-vad==6.2.0 --no-deps


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
	sudo rm -rf ~/.cache/ms-playwright
	sudo rm -rf /tmp/playwright-profile

.PHONY: test
test:
	espeak --stdout "this will speak" | ffplay -autoexit -f wav -i pipe:0
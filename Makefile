VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
REQ := requirements.txt

# -------------------------
# Default target
# -------------------------
.PHONY: help
help:
	@echo "Targets:"
	@echo "  make venv      Create virtual environment"
	@echo "  make install   Install Python dependencies"
	@echo "  make run       Run the voice assistant"
	@echo "  make clean     Remove virtual environment"

# -------------------------
# System dependencies (one-time)
# -------------------------
.PHONY: system-deps
system-deps:
	sudo apt update
	sudo apt install -y portaudio19-dev python3-dev

# -------------------------
# Setup virtual environment
# -------------------------
$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

venv: $(VENV)/bin/activate

# -------------------------
# Install dependencies
# -------------------------
.PHONY: install
install: venv
	$(PIP) install -r $(REQ)

# -------------------------
# Run listener
# -------------------------
.PHONY: run
run:
	$(PYTHON) main.py

# -------------------------
# Clean environment
# -------------------------
.PHONY: clean
clean:
	rm -rf $(VENV)

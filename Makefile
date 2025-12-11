# Scrapbot.AI Makefile

VENV=venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

install:
	@echo ">>> Creating virtual environment"
	python3 -m venv $(VENV)
	@echo ">>> Installing dependencies"
	$(PIP) install -r utilities/requirements.txt
	@echo ">>> Environment installed."

run:
	@echo ">>> Starting Scrapbot"
	$(PYTHON) main.py

parrot:
	@echo ">>> Testing Parrot Wake Word"
	$(PYTHON) parrot.py

whisper:
	@echo ">>> Testing Whisper-only transcription"
	$(PYTHON) whisper.py test

computer:
	@echo ">>> Testing Claude Computer Use"
	$(PYTHON) computer-use.py test

all: install run

update:
	@echo ">>> Updating dependencies"
	$(PIP) install --upgrade -r utilities/requirements.txt

clean:
	@echo ">>> Removing virtual environment"
	rm -rf $(VENV)
	@echo ">>> Done."c
#!/bin/bash
echo "[Scrapbot] Installing virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r utilities/requirements.txt
echo "[Scrapbot] Installation completed."
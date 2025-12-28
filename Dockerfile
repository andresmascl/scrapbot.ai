FROM python:3.12-slim

# 1. Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    python3-dev \
    gcc \
    libasound2-plugins \
    libasound2 \
    ffmpeg \
    libpulse0 \
    pulseaudio-utils \
    espeak \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Ensure Torch doesn't try to download models every time you restart
ENV TORCH_HOME=/home/scrapbot/.cache/torch

COPY requirements.txt .

# 2. Install Python dependencies
RUN python -m pip install --no-cache-dir --upgrade pip setuptools && \
    python -m pip install --no-cache-dir -r requirements.txt

# Pre-load the VAD model into the image to save startup time
RUN python3 -c "import torch; torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False, trust_repo=True)"

# 3. Finalize app structure
COPY . .

# Set up a non-root user for security (while keeping audio permissions)
RUN useradd -m -u 1000 scrapbot && \
    mkdir -p /home/scrapbot/.cache/torch && \
    chown -R scrapbot:scrapbot /home/scrapbot /app && \
    cp /app/asound.conf /home/scrapbot/.asoundrc && \
    chown scrapbot:scrapbot /home/scrapbot/.asoundrc

USER scrapbot

# 4. Entry point
CMD ["python", "main.py"]
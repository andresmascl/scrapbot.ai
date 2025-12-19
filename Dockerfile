# Use a Python 3.12 image
FROM python:3.12-slim

# 1. Install system dependencies for PyAudio and PortAudio
# Added --no-install-recommends to keep the image lean
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    python3-dev \
    gcc \
    libasound2-plugins \
    && rm -rf /var/lib/apt/lists/*

# 2. Set up working directory
WORKDIR /app

# 3. Set Torch Home environment variable
# This ensures the model is saved/loaded from a specific path during build AND run
ENV TORCH_HOME=/home/scrapbot/.cache/torch

# 4. Copy requirements and install
COPY requirements.txt .

# FIX: We use 'python -m pip' and separate the upgrade from the requirements install.
# We also omit 'wheel' as a separate requirement because modern pip handles this internally.
RUN python -m pip install --no-cache-dir --upgrade pip setuptools && \
    python -m pip install --no-cache-dir -r requirements.txt

# 5. PRE-DOWNLOAD MODELS
# We trigger the download during the BUILD phase so it's baked into the image.
# We set the TORCH_HOME here explicitly just in case, and trust the repo.
RUN python3 -c "import torch; torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=True, trust_repo=True)"

# 6. Copy the rest of your code
COPY . .

# 7. Run as a non-root user
# We create the directory first as root to ensure permissions are correct
RUN useradd -m -u 1000 scrapbot && \
    mkdir -p /home/scrapbot/.cache/torch && \
    chown -R scrapbot:scrapbot /home/scrapbot /app

USER scrapbot

CMD ["python", "main.py"]

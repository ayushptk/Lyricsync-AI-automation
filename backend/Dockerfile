# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
# ffmpeg is required for WhisperX and Basic Pitch
# git is required to install WhisperX from GitHub
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    libpq-dev \
    fluidsynth \
    fluid-soundfont-gm \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Deno — required by yt-dlp's EJS JavaScript challenge solver.
# yt-dlp uses Deno to solve YouTube's PO Token cryptographic challenges.
ENV DENO_INSTALL=/usr/local
RUN curl -fsSL https://deno.land/install.sh | sh

# Ensure Deno binary is on PATH (installed to /usr/local/bin/deno)
ENV PATH="/usr/local/bin:${PATH}"

# Ensure yt-dlp cache directory is writable.
# yt-dlp stores downloaded EJS challenge solver components here.
RUN mkdir -p /root/.cache/yt-dlp && chmod 755 /root/.cache/yt-dlp

# Clone bgutil-ytdlp-pot-provider for PO Tokens and install dependencies via Deno
RUN git clone --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /root/bgutil-ytdlp-pot-provider && \
    cd /root/bgutil-ytdlp-pot-provider/server && \
    deno install --allow-scripts=npm:canvas --frozen

# IMPORTANT: Do NOT create /etc/yt-dlp.conf with player_client=android.
# android is heavily restricted from AWS datacenter IPs.
# Player client selection is managed in the application code (services/youtube.py).

# Install python dependencies
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . .

# Command for FastAPI will be overridden in docker-compose.yml
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

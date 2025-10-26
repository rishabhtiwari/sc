FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Update package list and install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound-dev \
    git \
    wget \
    curl \
    # Install additional build dependencies required by some TTS packages
    build-essential \
    ffmpeg \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch first
RUN pip install torch==2.1.1 torchaudio==2.1.1

# Install Rust compiler and Cargo
# This is necessary to build sudachipy from source on ARM64.
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> "$HOME/.bashrc"

# Install TTS and xtts-api-server with Rust in PATH
RUN . "$HOME/.cargo/env" && pip install TTS==0.22.0
RUN . "$HOME/.cargo/env" && pip install xtts-api-server==0.9.0

# Install additional dependencies for our wrapper API
RUN pip install fastapi uvicorn python-multipart requests

# Copy our custom API wrapper
COPY voice_cloning_api.py /app/voice_cloning_api.py

# Create supervisor configuration
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create temporary directory (speakers and output will be mounted)
RUN mkdir -p /tmp/voice_cloning

# Expose ports
EXPOSE 8000 5003

# Use supervisor to run both services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

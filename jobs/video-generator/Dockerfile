# Video Generation Job Service
FROM python:3.9-slim

# Install system dependencies for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    pkg-config \
    wget \
    curl \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Configure ImageMagick security policy to allow text operations
RUN find /etc -name "policy.xml" -exec sed -i 's/<policy domain="path" rights="none" pattern="@\*"/<policy domain="path" rights="read|write" pattern="@*"/' {} \; || true

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY video-generator/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Configure MoviePy with proper config
RUN echo 'FFMPEG_BINARY = "/usr/bin/ffmpeg"' > /usr/local/lib/python3.9/site-packages/moviepy/config_defaults.py && \
    echo 'IMAGEMAGICK_BINARY = "/usr/bin/convert"' >> /usr/local/lib/python3.9/site-packages/moviepy/config_defaults.py

# Copy common job framework
COPY common/ /app/common/

# Copy application code
COPY video-generator/ .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/public /app/temp

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8095/health || exit 1

# Expose port
EXPOSE 8095

# Run the application
CMD ["python", "app.py"]

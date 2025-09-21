# Use Python 3.9 with CUDA support for better OCR performance
FROM python:3.9-slim

# Set metadata
LABEL maintainer="iChat Team"
LABEL description="Paddle OCR Document Converter Service"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=8081

# Install system dependencies for OCR including build tools
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r ocruser && useradd -r -g ocruser ocruser

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create necessary directories and set up user home
RUN mkdir -p /app/uploads /app/outputs /app/logs && \
    mkdir -p /home/ocruser/.paddleocr /home/ocruser/.config/matplotlib && \
    chown -R ocruser:ocruser /app /home/ocruser

# Copy application code
COPY . .

# Switch to non-root user
USER ocruser

# Expose port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Run the application
CMD ["python3", "app.py"]

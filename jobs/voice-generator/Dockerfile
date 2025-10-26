# Voice Generator Job Dockerfile
# Lightweight service that integrates with voice-cloning-service
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Audio processing for validation
    libsndfile1 \
    # Curl for health checks
    curl \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY voice-generator/requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy common job framework
COPY common /app/common
COPY common/models /app/models
COPY common/services /app/common_services
COPY common/utils /app/common_utils

# Set Python path to include common directories
ENV PYTHONPATH="/app:/app/common:/app/common/models:/app/common/services:/app/common/utils"

# Copy voice generator specific files
COPY voice-generator/config/ /app/config/
COPY voice-generator/services/ /app/services/
COPY voice-generator/utils/ /app/utils/
COPY voice-generator/app.py /app/

# Create necessary directories
RUN mkdir -p /app/data/reference_audio \
    /app/data/generated_audio \
    /app/logs

# Set permissions
RUN chmod -R 755 /app/data /app/logs

# Expose port
EXPOSE 8094

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8094/health || exit 1

# Run the application
CMD ["python", "app.py"]
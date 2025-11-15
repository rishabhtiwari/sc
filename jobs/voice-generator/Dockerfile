# Voice Generator Job Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY voice-generator/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy common modules
COPY common/ ./common/

# Copy voice-generator specific files
COPY voice-generator/ .

# Create symlinks for BaseJob imports
RUN ln -sf /app/common/services /app/services && \
    ln -sf /app/common/utils /app/utils

# Create necessary directories
RUN mkdir -p logs data public

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8094/health || exit 1

# Expose port
EXPOSE 8094

# Run the application
CMD ["python", "app.py"]

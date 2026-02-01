FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy common utilities first (for better caching)
COPY common /app/common

# Copy job-specific files
COPY image-auto-marker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY image-auto-marker /app

# Create necessary directories
RUN mkdir -p /var/log /app/logs

# Expose Flask port
EXPOSE 8102

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD curl -f http://localhost:8102/health || exit 1

# Run the job
CMD ["python", "app.py"]


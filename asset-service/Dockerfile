FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/temp

# Expose port
EXPOSE 8099

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8099/health || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for MinIO to be ready..."\n\
sleep 10\n\
echo "Initializing MinIO buckets..."\n\
python scripts/init_minio.py || echo "MinIO initialization failed (may already be initialized)"\n\
echo "Starting Asset Service..."\n\
exec uvicorn app:app --host 0.0.0.0 --port 8099 --workers 4\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/bin/bash", "/app/start.sh"]


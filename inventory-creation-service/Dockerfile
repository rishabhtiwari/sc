FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including ffmpeg for pydub audio processing)
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY inventory-creation-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY inventory-creation-service/ .

# Create logs and public directories
RUN mkdir -p /app/logs /app/public

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:5001/health || exit 1

# Create entrypoint script to fix permissions at runtime
RUN echo '#!/bin/bash\n\
mkdir -p /app/logs /app/public\n\
chmod 777 /app/logs /app/public\n\
exec python app.py' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Run the application via entrypoint
ENTRYPOINT ["/entrypoint.sh"]


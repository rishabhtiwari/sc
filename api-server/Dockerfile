# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set metadata
LABEL maintainer="iChat Team"
LABEL description="iChat API Server - Professional Flask API with MVC architecture"
LABEL version="2.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=8080

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs and data directories
# Note: When mounted as volumes, host permissions will apply
RUN mkdir -p /app/logs /app/data

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Create entrypoint script to fix permissions at runtime
RUN echo '#!/bin/bash\n\
mkdir -p /app/logs /app/data\n\
chmod 777 /app/logs /app/data\n\
exec python3 app.py' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Run the application via entrypoint
ENTRYPOINT ["/entrypoint.sh"]

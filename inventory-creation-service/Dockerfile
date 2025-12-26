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

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:5001/health || exit 1

# Run the application
CMD ["python", "app.py"]


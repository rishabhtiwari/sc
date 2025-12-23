FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including ffmpeg for pydub audio processing)
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY ecommerce-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ecommerce-service/app.py .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8099

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:8099/health || exit 1

# Run the application
CMD ["python", "app.py"]


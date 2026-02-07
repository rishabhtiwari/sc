FROM python:3.11-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY export-generator/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy common directory (shared job framework)
COPY common/ /app/common/

# Copy application code
COPY export-generator/config/ /app/config/
COPY export-generator/services/ /app/services/
COPY export-generator/app.py /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/exports /app/temp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=8101

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8101/health || exit 1

# Expose port
EXPOSE 8101

# Run the application
CMD ["python", "app.py"]


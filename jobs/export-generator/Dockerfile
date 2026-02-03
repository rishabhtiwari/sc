FROM python:3.11-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy common directory (shared job framework)
COPY ../common /app/common

# Copy application code
COPY config /app/config
COPY services /app/services
COPY app.py /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/exports /app/temp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=8100

# Expose port
EXPOSE 8100

# Run the application
CMD ["python", "app.py"]


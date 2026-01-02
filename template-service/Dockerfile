FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including FFmpeg for video processing and fonts for text rendering
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    ffmpeg \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/public /app/templates/news /app/templates/shorts /app/templates/ecommerce

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000
ENV PYTHONUNBUFFERED=1

# Create entrypoint script to fix permissions at runtime
RUN echo '#!/bin/bash\n\
mkdir -p /app/logs /app/public /app/templates\n\
chmod 777 /app/logs /app/public\n\
exec python app.py' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Run the application via entrypoint
ENTRYPOINT ["/entrypoint.sh"]


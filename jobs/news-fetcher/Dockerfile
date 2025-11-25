FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY news-fetcher/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy common framework first
COPY common ./common

# Copy application code
COPY news-fetcher/*.py .
COPY news-fetcher/config ./config
COPY news-fetcher/parsers ./parsers
COPY news-fetcher/services ./services
COPY news-fetcher/utils ./utils
COPY news-fetcher/templates ./templates
COPY news-fetcher/static ./static

# Create necessary directories
RUN mkdir -p logs data

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py

# Expose port
EXPOSE 8093

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8093/health || exit 1

# Run the application
CMD ["python", "app.py"]

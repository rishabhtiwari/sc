# Vector Database Service using ChromaDB
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user
RUN groupadd -r vectordb && useradd -r -g vectordb vectordb

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/logs /app/cache && \
    chown -R vectordb:vectordb /app && \
    mkdir -p /home/vectordb/.cache && \
    chown -R vectordb:vectordb /home/vectordb

# Set environment variables for caching
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/cache

# Switch to non-root user
USER vectordb

# Expose port
EXPOSE 8084

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8084/health || exit 1

# Start the application
CMD ["python", "app.py"]

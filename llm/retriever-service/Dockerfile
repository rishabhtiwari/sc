# Single-stage build for retriever service
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r retrieverservice && useradd -r -g retrieverservice retrieverservice

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/temp /home/retrieverservice/.cache && \
    chown -R retrieverservice:retrieverservice /app /home/retrieverservice

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/home/retrieverservice/.cache/huggingface
ENV TRANSFORMERS_CACHE=/home/retrieverservice/.cache/transformers

# Switch to non-root user
USER retrieverservice

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8086/health || exit 1

# Expose port
EXPOSE 8086

# Run the application
CMD ["python", "app.py"]

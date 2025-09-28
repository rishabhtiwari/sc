# Multi-stage build for LLM prompt generation service
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Create non-root user
RUN groupadd -r llmservice && useradd -r -g llmservice llmservice

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/llmservice/.local

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/temp /app/models /app/cache && \
    chown -R llmservice:llmservice /app

# Set environment variables
ENV PATH=/home/llmservice/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache

# Model Configuration - Change this to select different models
# Available options: flan-t5-base, flan-t5-small, flan-t5-large, mistral-7b-q4, mistral-7b-q5, mistral-7b-q2
ENV LLM_MODEL_KEY=mistral-7b-q4
ENV LLM_USE_GPU=false
ENV MODEL_CACHE_DIR=/app/cache

# Switch to non-root user
USER llmservice

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8087/health || exit 1

# Expose port
EXPOSE 8087

# Run the application
CMD ["python", "app.py"]

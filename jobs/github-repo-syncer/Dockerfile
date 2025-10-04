FROM python:3.9-slim

# Install git for repository cloning
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data and logs
RUN mkdir -p data logs

# Set environment variables
ENV PYTHONPATH=/app
ENV DOCKER_ENV=true

# Expose health check port
EXPOSE 8092

# Run the application
CMD ["python", "app.py"]

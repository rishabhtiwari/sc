FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy English model directly via pip
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/credentials

# Expose port
EXPOSE 8097

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_PORT=8097

# Run the application
CMD ["python", "app.py"]


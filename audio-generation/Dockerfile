# Use Node.js 18 LTS as base image
FROM node:18-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create data directory for model caching
RUN mkdir -p /app/data/models

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Copy application code
COPY . .

# Create volume mount point for persistent model storage
VOLUME ["/app/data"]

# Expose port
EXPOSE 3000

# Start the application
CMD ["node", "server.js"]

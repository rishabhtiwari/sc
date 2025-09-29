#!/bin/bash

# iChat UI Deployment Script
# This script builds and deploys the refactored iChat UI

set -e

echo "🚀 Starting iChat UI deployment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker-compose build ichat-ui

# Stop existing container if running
echo "🛑 Stopping existing container..."
docker-compose stop ichat-ui || true

# Start the new container
echo "▶️  Starting new container..."
docker-compose up ichat-ui -d

# Wait for health check
echo "🏥 Waiting for health check..."
sleep 5

# Check if container is healthy
if docker-compose ps ichat-ui | grep -q "healthy"; then
    echo "✅ Deployment successful!"
    echo "🌐 iChat UI is available at: http://localhost:3001"
    echo "🔗 Legacy UI is available at: http://localhost:3001/legacy"
    echo "💚 Health check: http://localhost:3001/health"
else
    echo "❌ Deployment failed - container is not healthy"
    echo "📋 Container logs:"
    docker-compose logs ichat-ui
    exit 1
fi

echo "🎉 Deployment complete!"

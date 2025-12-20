#!/bin/bash
set -e

echo "🚀 Starting Video Generator Service..."

# Create necessary directories
mkdir -p /app/logs /app/public /app/temp /app/subscribe /app/assets

# Create background music if it doesn't exist
if [ ! -f "/app/assets/background_music.wav" ]; then
    echo "🎵 Background music not found, creating it..."
    python /app/create_background_music.py
else
    echo "✅ Background music already exists"
fi

# Create logo if it doesn't exist
if [ ! -f "/app/assets/logo.png" ]; then
    echo "🎨 Logo not found, creating it..."
    python /app/create_sample_logo.py
else
    echo "✅ Logo already exists"
fi

echo "✅ Video Generator Service initialization complete"

# Execute the main command
exec "$@"


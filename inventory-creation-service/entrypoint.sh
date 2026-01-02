#!/bin/bash
# Entrypoint script to fix permissions for mounted volumes

# Create directories if they don't exist
mkdir -p /app/logs /app/public

# Set permissions to allow writing
chmod 777 /app/logs /app/public

# Execute the main application
exec python app.py


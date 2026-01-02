#!/bin/bash
# Entrypoint script to fix permissions for mounted volumes

# Create directories if they don't exist
mkdir -p /app/logs /app/data

# Set permissions to allow writing
chmod 777 /app/logs /app/data

# Execute the main application
exec python3 app.py


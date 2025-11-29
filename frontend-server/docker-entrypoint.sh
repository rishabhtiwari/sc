#!/bin/sh
# ============================================
# Docker Entrypoint Script
# ============================================
# Starts both Nginx and Node.js Express server
# ============================================

set -e

echo "=========================================="
echo "Starting News Automation Frontend"
echo "=========================================="

# Print environment variables
echo "Environment Configuration:"
echo "  PORT: ${PORT:-3002}"
echo "  API_SERVER_URL: ${API_SERVER_URL:-http://ichat-api-server:8080}"
echo "  NODE_ENV: ${NODE_ENV:-production}"
echo "=========================================="

# Start Node.js Express server in background
echo "Starting Express API proxy server on port ${PORT:-3002}..."
cd /app
node server.js &
NODE_PID=$!

# Wait for Express server to be ready
echo "Waiting for Express server to be ready..."
sleep 5

# Check if Express server is running
if ! kill -0 $NODE_PID 2>/dev/null; then
    echo "ERROR: Express server failed to start"
    exit 1
fi

echo "Express server started successfully (PID: $NODE_PID)"

# Start Nginx in foreground
echo "Starting Nginx web server..."
nginx -g 'daemon off;' &
NGINX_PID=$!

echo "Nginx started successfully (PID: $NGINX_PID)"
echo "=========================================="
echo "Frontend server is ready!"
echo "  - Nginx (static files): http://localhost:80"
echo "  - Express (API proxy): http://localhost:3002"
echo "=========================================="

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?


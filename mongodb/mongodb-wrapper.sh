#!/bin/bash

# MongoDB Wrapper Script
# Handles both fresh database initialization and existing database migrations

set -e

echo "=== MongoDB Wrapper: Starting MongoDB with Migration Support ==="

# Check if this is a fresh database (empty data directory)
if [ -z "$(ls -A /data/db 2>/dev/null)" ]; then
    echo "🆕 Fresh database detected - using MongoDB's initialization system"
    # For fresh databases, use MongoDB's standard initialization
    exec docker-entrypoint.sh "$@"
else
    echo "📁 Existing database detected - starting with migration check"
    
    # Start MongoDB in background
    echo "Starting MongoDB in background..."
    docker-entrypoint.sh "$@" &
    MONGODB_PID=$!
    
    # Wait for MongoDB to be ready
    echo "Waiting for MongoDB to be ready..."
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if mongosh --authenticationDatabase admin -u ichat_app -p ichat_app_password_2024 --eval "print('MongoDB ready')" > /dev/null 2>&1; then
            echo "✅ MongoDB is ready!"
            break
        fi
        echo "Attempt $attempt/$max_attempts: MongoDB not ready yet, waiting..."
        sleep 2
        attempt=$((attempt + 1))
        
        if [ $attempt -gt $max_attempts ]; then
            echo "❌ MongoDB failed to start within expected time"
            kill $MONGODB_PID 2>/dev/null || true
            exit 1
        fi
    done
    
    # Run migrations for existing database
    echo "🔄 Running migration check for existing database..."
    if [ -f "/app/scripts/run-migrations.sh" ]; then
        if /app/scripts/run-migrations.sh; then
            echo "✅ Migration check completed successfully"
        else
            echo "⚠️  Migration check completed with warnings (this might be normal)"
        fi
    else
        echo "⚠️  No migration script found"
    fi
    
    echo "✅ MongoDB startup and migration check complete"
    
    # Wait for MongoDB process to finish (keep container running)
    wait $MONGODB_PID
fi

#!/bin/bash

echo "🚀 Starting Auth Service..."

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB..."
until nc -z ichat-mongodb 27017; do
    echo "MongoDB is unavailable - sleeping"
    sleep 2
done
echo "✅ MongoDB is ready!"

# Start the Flask application
echo "🔥 Starting Flask application..."
python app.py


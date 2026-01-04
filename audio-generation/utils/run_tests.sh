#!/bin/bash
# Script to build and run unit tests in Docker container

set -e

echo "🐳 Building Docker test container..."
docker build -f Dockerfile.test -t text-chunker-test .

echo ""
echo "🧪 Running unit tests..."
docker run --rm text-chunker-test

echo ""
echo "✅ Tests completed!"


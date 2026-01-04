#!/bin/bash
# Script to build and run unit tests with coverage in Docker container

set -e

echo "🐳 Building Docker test container..."
docker build -f Dockerfile.test -t text-chunker-test .

echo ""
echo "🧪 Running unit tests with coverage..."
docker run --rm text-chunker-test \
    python -m pytest test_text_chunker.py -v --tb=short \
    --cov=text_chunker \
    --cov-report=term-missing \
    --cov-report=html

echo ""
echo "✅ Tests completed with coverage report!"


#!/bin/bash

# OCR Service Test Script
# This script demonstrates how to use the OCR service for document parsing

OCR_URL="http://localhost:8081"
TEST_DIR="test-files"

echo "🧪 OCR Service Document Parsing Test"
echo "===================================="

# Check if service is running
echo "📡 Checking OCR service health..."
curl -s "$OCR_URL/health" | jq .status

echo -e "\n📋 Available formats:"
curl -s "$OCR_URL/formats" | jq .supported_formats

echo -e "\n🔍 Testing document parsing..."

# Test 1: Parse an image (you need to provide your own test image)
if [ -f "$TEST_DIR/sample.png" ]; then
    echo -e "\n1️⃣ Parsing PNG image..."
    curl -X POST "$OCR_URL/convert" \
        -F "file=@$TEST_DIR/sample.png" \
        -F "output_format=text" \
        -F "language=en"
fi

# Test 2: Parse a PDF (you need to provide your own test PDF)
if [ -f "$TEST_DIR/sample.pdf" ]; then
    echo -e "\n2️⃣ Parsing PDF document..."
    curl -X POST "$OCR_URL/convert" \
        -F "file=@$TEST_DIR/sample.pdf" \
        -F "output_format=json" \
        -F "language=en" | jq .
fi

# Test 3: Parse with different output formats
if [ -f "$TEST_DIR/sample.jpg" ]; then
    echo -e "\n3️⃣ Parsing with markdown output..."
    curl -X POST "$OCR_URL/convert" \
        -F "file=@$TEST_DIR/sample.jpg" \
        -F "output_format=markdown" \
        -F "language=en"
fi

echo -e "\n✅ Test completed!"
echo "💡 To use this script:"
echo "   1. Create a 'test-files' directory"
echo "   2. Add sample images (PNG, JPG) or PDFs"
echo "   3. Run: ./test-ocr.sh"

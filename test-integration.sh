#!/bin/bash

# Test script for iChat API Server + OCR Service Integration
# This script demonstrates the complete integration between chat and document processing

echo "🧪 iChat API Server + OCR Service Integration Test"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test URLs
API_SERVER="http://localhost:8080"
OCR_SERVICE="http://localhost:8081"

echo -e "${BLUE}1. Testing Service Health${NC}"
echo "----------------------------"

echo "📡 API Server Health:"
curl -s "$API_SERVER/api/health" | jq -r '.message, .status' || echo "❌ API Server not responding"

echo ""
echo "🔍 OCR Service Health:"
curl -s "$OCR_SERVICE/health" | jq -r '.message, .status' || echo "❌ OCR Service not responding"

echo ""
echo -e "${BLUE}2. Testing Document Detection in Chat${NC}"
echo "----------------------------------------"

# Test document-related queries
declare -a document_queries=(
    "Can you help me read a PDF document?"
    "I need to extract text from an image"
    "Please OCR this document for me"
    "How do I scan a document?"
    "Can you analyze this PDF file?"
)

declare -a regular_queries=(
    "Hello, how are you?"
    "What's the weather like?"
    "Tell me a joke"
)

echo "📄 Document-related queries:"
for query in "${document_queries[@]}"; do
    echo ""
    echo "Query: '$query'"
    response=$(curl -s -X POST "$API_SERVER/api/chat" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"client\": \"test\"}" | jq -r '.message')
    
    if [[ $response == *"OCR service"* ]] || [[ $response == *"document"* ]] || [[ $response == *"upload"* ]]; then
        echo -e "${GREEN}✅ Detected as document query${NC}"
    else
        echo -e "${RED}❌ Not detected as document query${NC}"
    fi
    echo "Response: ${response:0:100}..."
done

echo ""
echo "💬 Regular chat queries:"
for query in "${regular_queries[@]}"; do
    echo ""
    echo "Query: '$query'"
    response=$(curl -s -X POST "$API_SERVER/api/chat" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$query\", \"client\": \"test\"}" | jq -r '.message')
    
    if [[ $response == *"OCR service"* ]] || [[ $response == *"document"* ]] || [[ $response == *"upload"* ]]; then
        echo -e "${RED}❌ Incorrectly detected as document query${NC}"
    else
        echo -e "${GREEN}✅ Correctly handled as regular chat${NC}"
    fi
    echo "Response: ${response:0:100}..."
done

echo ""
echo -e "${BLUE}3. Testing Document Processing Endpoints${NC}"
echo "--------------------------------------------"

echo "📋 Supported formats:"
curl -s "$API_SERVER/api/documents/formats" | jq '.data.supported_formats'

echo ""
echo "🔧 OCR Service status:"
curl -s "$API_SERVER/api/documents/status" | jq '.ocr_service.status'

echo ""
echo "📖 Document help:"
curl -s "$API_SERVER/api/documents/help" | jq -r '.message'

echo ""
echo -e "${BLUE}4. Testing Query Analysis${NC}"
echo "----------------------------"

test_query="I need to extract text from this PDF document"
echo "Analyzing query: '$test_query'"
curl -s -X POST "$API_SERVER/api/documents/analyze" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$test_query\"}" | jq '.intent'

echo ""
echo -e "${BLUE}5. Integration Summary${NC}"
echo "------------------------"

# Check if both services are running
api_health=$(curl -s "$API_SERVER/api/health" | jq -r '.status' 2>/dev/null)
ocr_health=$(curl -s "$OCR_SERVICE/health" | jq -r '.status' 2>/dev/null)
integration_health=$(curl -s "$API_SERVER/api/documents/status" | jq -r '.ocr_service.status' 2>/dev/null)

echo "Service Status:"
if [ "$api_health" = "healthy" ]; then
    echo -e "  ${GREEN}✅ API Server: Running${NC}"
else
    echo -e "  ${RED}❌ API Server: Not responding${NC}"
fi

if [ "$ocr_health" = "success" ]; then
    echo -e "  ${GREEN}✅ OCR Service: Running${NC}"
else
    echo -e "  ${RED}❌ OCR Service: Not responding${NC}"
fi

if [ "$integration_health" = "healthy" ]; then
    echo -e "  ${GREEN}✅ Service Integration: Working${NC}"
else
    echo -e "  ${RED}❌ Service Integration: Failed${NC}"
fi

echo ""
echo "Available Endpoints:"
echo "  📡 Chat: POST $API_SERVER/api/chat"
echo "  📄 Document Upload: POST $API_SERVER/api/documents/upload"
echo "  📋 Document Formats: GET $API_SERVER/api/documents/formats"
echo "  🔍 Document Status: GET $API_SERVER/api/documents/status"
echo "  📖 Document Help: GET $API_SERVER/api/documents/help"
echo "  ❤️  Health Check: GET $API_SERVER/api/health"

echo ""
echo -e "${GREEN}🎉 Integration test complete!${NC}"
echo ""
echo "To test document upload:"
echo "curl -X POST $API_SERVER/api/documents/upload \\"
echo "  -F \"file=@your-document.pdf\" \\"
echo "  -F \"output_format=json\" \\"
echo "  -F \"language=en\""

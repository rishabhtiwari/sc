#!/bin/bash

################################################################################
# Coqui TTS Model Initialization Script
#
# This script initializes the Coqui TTS service by downloading the XTTS-v2 model
# if it hasn't been downloaded yet. This prevents the service from failing on
# first startup due to missing model files.
#
# Usage:
#   ./scripts/init-coqui-tts.sh [--gpu]
#
# Options:
#   --gpu    Use GPU-enabled configuration
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

print_error() {
    echo -e "${RED}✗ ${NC}$1"
}

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Parse arguments
USE_GPU=false
if [ "$1" = "--gpu" ]; then
    USE_GPU=true
fi

print_header "Coqui TTS Model Initialization"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_success "Docker is running"

# Check if coqui-tts service is defined
COMPOSE_CMD="docker-compose"
if [ "$USE_GPU" = true ]; then
    COMPOSE_CMD="docker-compose -f docker-compose.yml -f docker-compose.gpu.yml"
    print_info "Using GPU configuration"
fi

# Check if service exists
if ! $COMPOSE_CMD config --services | grep -q "coqui-tts"; then
    print_error "coqui-tts service not found in docker-compose configuration"
    exit 1
fi

print_success "coqui-tts service found in configuration"

# Pull the latest image
print_info "Pulling Coqui TTS Docker image..."
docker pull ghcr.io/coqui-ai/tts:latest
print_success "Image pulled successfully"

# Check if models are already downloaded
print_info "Checking if XTTS-v2 model is already downloaded..."

# Create a temporary container to check for models
VOLUME_NAME="sc_coqui-tts-models"
MODEL_CHECK=$(docker run --rm -v ${VOLUME_NAME}:/root/.local/share/tts alpine sh -c "ls -la /root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/config.json 2>/dev/null || echo 'NOT_FOUND'")

if echo "$MODEL_CHECK" | grep -q "NOT_FOUND"; then
    print_warning "XTTS-v2 model not found. Downloading..."
    
    # Download the model by running a temporary TTS command
    print_info "This may take several minutes (model is ~2GB)..."
    
    docker run --rm \
        -v ${VOLUME_NAME}:/root/.local/share/tts \
        ghcr.io/coqui-ai/tts:latest \
        tts --model_name tts_models/multilingual/multi-dataset/xtts_v2 \
        --text "Initialization test" \
        --out_path /tmp/init.wav
    
    print_success "Model downloaded successfully!"
else
    print_success "XTTS-v2 model already exists"
fi

# Verify model files
print_info "Verifying model files..."
VERIFY=$(docker run --rm -v ${VOLUME_NAME}:/root/.local/share/tts alpine sh -c "ls /root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/ | wc -l")

if [ "$VERIFY" -gt 0 ]; then
    print_success "Model files verified (found $VERIFY files)"
else
    print_error "Model verification failed"
    exit 1
fi

print_header "Initialization Complete"
print_success "Coqui TTS is ready to use!"
echo ""
print_info "You can now start the service with:"
if [ "$USE_GPU" = true ]; then
    echo "  docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d coqui-tts"
else
    echo "  docker-compose up -d coqui-tts"
fi
echo ""
print_info "Or use the deployment script:"
if [ "$USE_GPU" = true ]; then
    echo "  ./deploy-news-services.sh --service coqui-tts --gpu"
else
    echo "  ./deploy-news-services.sh --service coqui-tts"
fi
echo ""


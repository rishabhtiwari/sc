#!/bin/bash

################################################################################
# Audio Generation Factory GPU Deployment Script
#
# This script deploys the audio-generation-factory service to a GPU instance
# for faster Bark model loading and inference.
#
# Usage:
#   ./deploy-audio-to-gpu.sh [options]
#
# Options:
#   --build         Force rebuild of the Docker image
#   --logs          Show logs after deployment
#   --status        Show status of the service
#   --stop          Stop the service on GPU instance
#   --help          Show this help message
################################################################################

set -e  # Exit on error

# Configuration
GPU_HOST="120.238.149.205"
GPU_PORT="27268"
GPU_USER="root"
SSH_KEY="$HOME/.ssh/vast"
SERVICE_NAME="audio-generation-factory"
IMAGE_NAME="sc-audio-generation-factory"
CONTAINER_NAME="audio-generation-factory"
HOST_PORT="3000"
CONTAINER_PORT="3000"

# SSH command with key and port
SSH_CMD="ssh -i ${SSH_KEY} -p ${GPU_PORT}"
SCP_CMD="scp -i ${SSH_KEY} -P ${GPU_PORT}"

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

# Function to check SSH connectivity
check_ssh() {
    print_info "Checking SSH connectivity to GPU instance..."
    print_info "Using SSH key: ${SSH_KEY}"

    if [ ! -f "${SSH_KEY}" ]; then
        print_error "SSH key not found at ${SSH_KEY}"
        exit 1
    fi

    if ${SSH_CMD} -o ConnectTimeout=5 -o BatchMode=yes "${GPU_USER}@${GPU_HOST}" exit 2>/dev/null; then
        print_success "SSH connection successful"
        return 0
    else
        print_error "Cannot connect to GPU instance via SSH"
        print_info "Please ensure:"
        echo "  1. SSH key exists at ${SSH_KEY}"
        echo "  2. GPU instance is running and accessible"
        echo "  3. Firewall allows SSH connections"
        exit 1
    fi
}

# Function to build Docker image
build_image() {
    print_header "Building Docker Image for AMD64 Platform"
    print_info "Building ${IMAGE_NAME} for linux/amd64..."

    # Build for AMD64 platform (GPU instance architecture)
    docker buildx build --platform linux/amd64 \
        -t ${IMAGE_NAME}:latest \
        -f audio-generation/Dockerfile \
        audio-generation/

    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Function to save and transfer image
transfer_image() {
    print_header "Transferring Docker Image to GPU Instance"

    local image_file="/tmp/${IMAGE_NAME}.tar"

    print_info "Saving Docker image to ${image_file}..."
    docker save ${IMAGE_NAME}:latest -o ${image_file}
    print_success "Image saved"

    print_info "Transferring image to GPU instance (this may take a few minutes)..."
    ${SCP_CMD} ${image_file} "${GPU_USER}@${GPU_HOST}:/tmp/"
    print_success "Image transferred"

    print_info "Cleaning up local image file..."
    rm ${image_file}
    print_success "Cleanup complete"
}

# Function to deploy on GPU instance
deploy_on_gpu() {
    print_header "Deploying on GPU Instance"

    print_info "Loading Docker image on GPU instance..."
    ${SSH_CMD} "${GPU_USER}@${GPU_HOST}" "docker load -i /tmp/${IMAGE_NAME}.tar && rm /tmp/${IMAGE_NAME}.tar"
    print_success "Image loaded"

    print_info "Stopping existing container (if any)..."
    ${SSH_CMD} "${GPU_USER}@${GPU_HOST}" "docker stop ${CONTAINER_NAME} 2>/dev/null || true"
    ${SSH_CMD} "${GPU_USER}@${GPU_HOST}" "docker rm ${CONTAINER_NAME} 2>/dev/null || true"

    print_info "Starting new container with GPU support..."
    ${SSH_CMD} "${GPU_USER}@${GPU_HOST}" "docker run -d \
        --name ${CONTAINER_NAME} \
        --gpus all \
        -p ${HOST_PORT}:${CONTAINER_PORT} \
        -v audio-generation-data:/app/data \
        --restart unless-stopped \
        ${IMAGE_NAME}:latest"

    print_success "Container started"
}

# Function to show logs
show_logs() {
    print_header "Showing Logs from GPU Instance"
    print_info "Connecting to GPU instance and streaming logs..."
    print_info "Press Ctrl+C to stop"
    echo ""
    ${SSH_CMD} "${GPU_USER}@${GPU_HOST}" "docker logs -f --tail=100 ${CONTAINER_NAME}"
}

# Function to show status
show_status() {
    print_header "Service Status on GPU Instance"

    print_info "Checking container status..."
    ${SSH_CMD} "${GPU_USER}@${GPU_HOST}" "docker ps -a --filter name=${CONTAINER_NAME} --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

    echo ""
    print_info "Checking GPU availability..."
    ${SSH_CMD} "${GPU_USER}@${GPU_HOST}" "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo 'nvidia-smi not available'"

    echo ""
    print_info "Recent logs:"
    ${SSH_CMD} "${GPU_USER}@${GPU_HOST}" "docker logs --tail=20 ${CONTAINER_NAME} 2>&1"
}

# Function to stop service
stop_service() {
    print_header "Stopping Service on GPU Instance"

    print_info "Stopping container..."
    ${SSH_CMD} "${GPU_USER}@${GPU_HOST}" "docker stop ${CONTAINER_NAME}"
    print_success "Container stopped"

    print_info "Removing container..."
    ${SSH_CMD} "${GPU_USER}@${GPU_HOST}" "docker rm ${CONTAINER_NAME}"
    print_success "Container removed"
}

# Function to show help
show_help() {
    cat << EOF
Audio Generation Factory GPU Deployment Script

This script deploys the audio-generation-factory service to a GPU instance
for faster Bark model loading and inference.

Configuration:
  GPU Host:       ${GPU_HOST}
  GPU User:       ${GPU_USER}
  Service Port:   ${HOST_PORT}

Usage:
  ./deploy-audio-to-gpu.sh [options]

Options:
  --build         Force rebuild of the Docker image before deployment
  --logs          Show logs from the GPU instance
  --status        Show status of the service on GPU instance
  --stop          Stop the service on GPU instance
  --help          Show this help message

Examples:
  # Deploy to GPU instance
  ./deploy-audio-to-gpu.sh

  # Rebuild and deploy
  ./deploy-audio-to-gpu.sh --build

  # Check status
  ./deploy-audio-to-gpu.sh --status

  # View logs
  ./deploy-audio-to-gpu.sh --logs

  # Stop service
  ./deploy-audio-to-gpu.sh --stop

EOF
}

# Main deployment function
deploy() {
    local build_flag=$1

    print_header "Audio Generation Factory - GPU Deployment"

    # Check SSH connectivity
    check_ssh

    # Build image if requested or if it doesn't exist
    if [ "$build_flag" = "--build" ] || ! docker images ${IMAGE_NAME} | grep -q ${IMAGE_NAME}; then
        build_image
    else
        print_info "Using existing Docker image (use --build to rebuild)"
    fi

    # Transfer image to GPU instance
    transfer_image

    # Deploy on GPU instance
    deploy_on_gpu

    # Show status
    echo ""
    show_status

    echo ""
    print_success "Deployment complete!"
    echo ""
    print_info "Service URL: http://${GPU_HOST}:${HOST_PORT}"
    print_info "To view logs: ./deploy-audio-to-gpu.sh --logs"
    print_info "To check status: ./deploy-audio-to-gpu.sh --status"
    echo ""
}

# Main script logic
main() {
    case "${1:-}" in
        --build)
            deploy "--build"
            ;;
        --logs)
            show_logs
            ;;
        --status)
            show_status
            ;;
        --stop)
            stop_service
            ;;
        --help|-h)
            show_help
            ;;
        "")
            deploy ""
            ;;
        *)
            print_error "Unknown option: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"



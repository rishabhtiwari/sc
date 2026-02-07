#!/bin/bash

################################################################################
# News Services Deployment Script
#
# This script deploys all news-related services in the correct order:
# 1. MongoDB (database)
# 2. MinIO (object storage)
# 3. Auth Service (authentication and user management)
# 4. Template Service (video templates management)
# 5. Asset Service (asset management with MinIO)
# 6. News Fetcher Job (fetches news articles)
# 7. LLM Service (generates summaries)
# 8. Coqui TTS Server (XTTS-v2 model for multilingual TTS)
# 9. Audio Generation Factory (TTS models: Kokoro for English, Veena for Hindi)
# 10. Voice Generator Job (generates audio from news)
# 11. IOPaint Watermark Remover (removes watermarks from images - GPU)
# 12. Image Auto-Marker Job (automatically marks images as cleaned)
# 13. Video Generator Job (creates videos from news + audio)
# 14. Export Generator Job (exports videos in different formats)
# 15. YouTube Uploader (uploads videos to YouTube)
# 16. Cleanup Job (cleans up old files and MongoDB records)
# 17. E-commerce Service (manages e-commerce products and video generation)
# 18. API Server (serves news data to frontend)
# 19. News Automation Frontend (React UI for managing news automation)
#
# Usage:
#   ./deploy-news-services.sh [options] [service_name]
#
# Options:
#   --build         Force rebuild of all services
#   --gpu           Enable GPU support for compatible services (LLM, Audio, IOPaint)
#   --logs [svc]    Show logs (optionally for specific service)
#   --status        Show status of all services
#   --stop [svc]    Stop all services or specific service
#   --restart [svc] Restart all services or specific service
#   --service <name> Deploy only specific service
#   --help          Show this help message
#
# Examples:
#   ./deploy-news-services.sh --build                    # Deploy all with rebuild
#   ./deploy-news-services.sh --build --gpu              # Deploy all with GPU support
#   ./deploy-news-services.sh --service llm-service      # Deploy only LLM service
#   ./deploy-news-services.sh --service llm-service --gpu --build  # Deploy LLM with GPU
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global flags
USE_GPU=false
SINGLE_SERVICE=""

# Service names
SERVICES=(
    "ichat-mongodb"
    "minio"
    "auth-service"
    "template-service"
    "asset-service"
    "job-news-fetcher"
    "llm-service"
    "coqui-tts"
    "audio-generation-factory"
    "job-voice-generator"
    "iopaint"
    "job-image-auto-marker"
    "job-video-generator"
    "job-export-generator"
    "youtube-uploader"
    "job-cleanup"
    "inventory-creation-service"
    "ichat-api"
    "news-automation-frontend"
)

# GPU-capable services
GPU_SERVICES=(
    "llm-service"
    "coqui-tts"
    "audio-generation-factory"
    "iopaint"
)

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

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to wait for apt lock to be released
wait_for_apt_lock() {
    local max_wait=300  # 5 minutes
    local waited=0

    while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || \
          sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1 || \
          sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do

        if [ $waited -ge $max_wait ]; then
            print_error "Timeout waiting for apt lock to be released."
            print_info "Another process (likely unattended-upgrades) is using apt."
            print_info "You can manually stop it with: sudo systemctl stop unattended-upgrades"
            return 1
        fi

        if [ $waited -eq 0 ]; then
            print_info "Waiting for apt lock to be released (another process is using apt)..."
        fi

        sleep 5
        waited=$((waited + 5))

        if [ $((waited % 30)) -eq 0 ]; then
            print_info "Still waiting... ($waited seconds elapsed)"
        fi
    done

    return 0
}

# Function to install NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    print_header "Installing NVIDIA Container Toolkit"

    # Check if nvidia-container-toolkit is already installed and configured
    if command -v nvidia-ctk &> /dev/null; then
        print_success "NVIDIA Container Toolkit is already installed"
        nvidia-ctk --version 2>/dev/null || true

        # Check if Docker is already configured for NVIDIA runtime
        if grep -q "nvidia" /etc/docker/daemon.json 2>/dev/null; then
            print_success "Docker is already configured for NVIDIA runtime"
            print_info "Skipping reconfiguration"
            return 0
        else
            print_info "Configuring Docker to use NVIDIA Container Runtime..."
            sudo nvidia-ctk runtime configure --runtime=docker

            print_info "Restarting Docker daemon..."
            sudo systemctl restart docker
            sleep 3

            return 0
        fi
    fi

    # Detect OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        print_error "Cannot detect OS. Please install NVIDIA Container Toolkit manually."
        return 1
    fi

    print_info "Detected OS: $OS"

    case "$OS" in
        ubuntu|debian)
            # Wait for apt lock if needed
            if ! wait_for_apt_lock; then
                return 1
            fi

            print_info "Installing prerequisites..."
            sudo apt-get update && sudo apt-get install -y --no-install-recommends curl gnupg2

            print_info "Configuring NVIDIA Container Toolkit repository..."
            curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
            curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
                sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
                sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

            print_info "Installing NVIDIA Container Toolkit..."
            sudo apt-get update
            sudo apt-get install -y nvidia-container-toolkit
            ;;

        rhel|centos|fedora|amzn)
            print_info "Installing prerequisites..."
            sudo dnf install -y curl

            print_info "Configuring NVIDIA Container Toolkit repository..."
            curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
                sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

            print_info "Installing NVIDIA Container Toolkit..."
            sudo dnf install -y nvidia-container-toolkit
            ;;

        opensuse*|sles)
            print_info "Configuring NVIDIA Container Toolkit repository..."
            sudo zypper ar https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo

            print_info "Installing NVIDIA Container Toolkit..."
            sudo zypper --gpg-auto-import-keys install -y nvidia-container-toolkit
            ;;

        *)
            print_error "Unsupported OS: $OS"
            print_error "Please install NVIDIA Container Toolkit manually:"
            print_error "https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html"
            return 1
            ;;
    esac

    # Configure Docker to use NVIDIA runtime
    print_info "Configuring Docker to use NVIDIA Container Runtime..."
    sudo nvidia-ctk runtime configure --runtime=docker

    # Disable persistence mode requirement in NVIDIA runtime config
    print_info "Configuring NVIDIA runtime to not require persistence daemon..."
    if [ -f /etc/nvidia-container-runtime/config.toml ]; then
        # Set no-cgroups = false to disable persistence daemon requirement
        sudo sed -i 's/#no-cgroups = false/no-cgroups = false/' /etc/nvidia-container-runtime/config.toml 2>/dev/null || true
        sudo sed -i 's/no-cgroups = true/no-cgroups = false/' /etc/nvidia-container-runtime/config.toml 2>/dev/null || true
    fi

    # Try to start NVIDIA persistence daemon (optional)
    print_info "Attempting to start NVIDIA persistence daemon..."
    sudo systemctl stop nvidia-persistenced 2>/dev/null || true
    sudo killall nvidia-persistenced 2>/dev/null || true

    sudo mkdir -p /run/nvidia-persistenced
    sudo chmod 755 /run/nvidia-persistenced

    # Try to start - ignore if it fails
    if ! pgrep -x nvidia-persiste > /dev/null; then
        sudo nohup nvidia-persistenced --persistence-mode > /var/log/nvidia-persistenced.log 2>&1 &
        sleep 2
    fi

    # Restart Docker
    print_info "Restarting Docker daemon..."
    sudo systemctl restart docker

    # Wait for Docker to fully restart
    print_info "Waiting for Docker to fully restart..."
    sleep 5

    print_success "NVIDIA Container Toolkit installed and configured successfully!"
    return 0
}

# Function to check GPU availability
check_gpu() {
    if [ "$USE_GPU" = true ]; then
        print_info "Checking GPU availability..."

        # Check if nvidia-smi is available
        if ! command -v nvidia-smi &> /dev/null; then
            print_error "nvidia-smi not found. NVIDIA GPU drivers are not installed."
            print_error "Please install NVIDIA drivers first:"
            print_error "https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html"
            exit 1
        fi

        # Set up NVIDIA persistence daemon or create dummy socket
        print_info "Setting up NVIDIA persistence daemon..."

        # Stop any existing instance first
        sudo systemctl stop nvidia-persistenced 2>/dev/null || true
        sudo killall nvidia-persistenced 2>/dev/null || true
        sleep 1

        # Create socket directory
        sudo mkdir -p /run/nvidia-persistenced
        sudo chmod 755 /run/nvidia-persistenced

        # Method 1: Try to load nvidia kernel module first
        print_info "Loading NVIDIA kernel modules..."
        sudo modprobe nvidia 2>/dev/null || true
        sudo nvidia-modprobe -u -c=0 2>/dev/null || true
        sleep 1

        # Method 2: Try to start the daemon
        if ! pgrep -x nvidia-persiste > /dev/null; then
            print_info "Starting NVIDIA persistence daemon..."
            # Try without --persistence-mode flag first
            sudo nvidia-persistenced --verbose > /var/log/nvidia-persistenced.log 2>&1 &
            sleep 3

            # If that didn't work, try with --persistence-mode
            if [ ! -S /run/nvidia-persistenced/socket ]; then
                sudo killall nvidia-persistenced 2>/dev/null || true
                sudo nvidia-persistenced --persistence-mode --verbose > /var/log/nvidia-persistenced.log 2>&1 &
                sleep 3
            fi
        fi

        # Check if socket was created
        if [ -S /run/nvidia-persistenced/socket ]; then
            print_success "NVIDIA persistence daemon socket created successfully"
        else
            print_warning "Failed to create persistence daemon socket"
            print_info "Checking logs..."
            tail -5 /var/log/nvidia-persistenced.log 2>/dev/null || true

            # Method 3: Create a dummy socket as workaround
            print_info "Creating dummy socket as workaround..."
            sudo rm -f /run/nvidia-persistenced/socket
            # Use socat to create a dummy unix socket that just accepts connections
            sudo nohup socat UNIX-LISTEN:/run/nvidia-persistenced/socket,fork,mode=666 - > /dev/null 2>&1 &
            sleep 1

            if [ -S /run/nvidia-persistenced/socket ]; then
                print_success "Dummy socket created (containers should start now)"
            else
                print_error "Failed to create socket. GPU containers may not start."
            fi
        fi

        # Check if NVIDIA Docker runtime is available
        if ! docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null 2>&1; then
            print_warning "NVIDIA Container Toolkit not available or not configured."
            print_info "Attempting to install NVIDIA Container Toolkit..."

            if install_nvidia_container_toolkit; then
                print_success "NVIDIA Container Toolkit installed successfully!"

                # Wait for Docker to fully restart
                print_info "Waiting for Docker to fully restart..."
                sleep 5

                # Verify installation with retries
                local max_retries=3
                local retry=0
                local verified=false

                while [ $retry -lt $max_retries ]; do
                    if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null 2>&1; then
                        verified=true
                        break
                    fi
                    retry=$((retry + 1))
                    if [ $retry -lt $max_retries ]; then
                        print_info "Verification attempt $retry failed, retrying..."
                        sleep 3
                    fi
                done

                if [ "$verified" = false ]; then
                    print_error "NVIDIA Container Toolkit installation failed verification after $max_retries attempts."
                    print_info "This might be a temporary issue. Trying to continue anyway..."
                    print_info "If GPU services fail to start, please run: sudo systemctl restart docker"
                fi
            else
                print_error "Failed to install NVIDIA Container Toolkit."
                print_error "Please install it manually and try again."
                exit 1
            fi
        fi

        print_success "GPU support is available"
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | while read line; do
            print_info "  GPU: $line"
        done
        return 0
    fi
}

# Function to check if service supports GPU
is_gpu_service() {
    local service=$1
    for gpu_svc in "${GPU_SERVICES[@]}"; do
        if [ "$service" = "$gpu_svc" ]; then
            return 0
        fi
    done
    return 1
}

# Function to check .env file
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found!"
        print_info "Creating .env file from .env.template..."

        if [ -f ".env.template" ]; then
            cp .env.template .env
            print_warning "Please edit .env file and add your API keys:"
            print_warning "  - HUGGINGFACE_HUB_TOKEN (get from: https://huggingface.co/settings/tokens)"
            print_warning "  - GNEWS_API_KEY (get from: https://gnews.io/)"
            print_error "Exiting. Please configure .env file and run again."
            exit 1
        else
            print_error ".env.template not found. Cannot create .env file."
            exit 1
        fi
    else
        # Check if required variables are set
        if grep -q "your_huggingface_token_here" .env || grep -q "your_gnews_api_key_here" .env; then
            print_warning "⚠️  .env file contains placeholder values!"
            print_warning "Please update .env file with your actual API keys:"
            print_warning "  - HUGGINGFACE_HUB_TOKEN (get from: https://huggingface.co/settings/tokens)"
            print_warning "  - GNEWS_API_KEY (get from: https://gnews.io/)"
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        else
            print_success ".env file found and configured"
        fi
    fi
}

# Function to create necessary directories
create_directories() {
    print_info "Creating necessary directories..."

    # List of directories that need to exist
    local dirs=(
        "mongodb/data"
        "mongodb/logs"
        "api-server/logs"
        "api-server/data"
        "frontend-server/logs"
        "frontend-server/data"
        "template-service/logs"
        "template-service/public"
        "inventory-creation-service/logs"
        "inventory-creation-service/public"
        "auth-service/logs"
        "asset-service/logs"
        "asset-service/temp"
        "llm/llm-prompt-generation/cache"
        "llm/llm-prompt-generation/logs"
        "jobs/news-fetcher/logs"
        "jobs/news-fetcher/data"
        "jobs/voice-generator/logs"
        "jobs/voice-generator/data"
        "jobs/video-generator/logs"
        "jobs/video-generator/public"
        "jobs/video-generator/temp"
        "jobs/video-generator/assets"
        "jobs/export-generator/logs"
        "jobs/export-generator/temp"
        "jobs/youtube-uploader/logs"
        "jobs/youtube-uploader/credentials"
        "jobs/cleanup/logs"
        "jobs/watermark-remover/public"
        "jobs/watermark-remover/models"
        "jobs/image-auto-marker/logs"
        "audio-generation/data"
        "audio-generation/public"
        "coqui-tts-models"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            # Set permissions to allow Docker containers to write
            chmod 777 "$dir"
            print_success "Created directory: $dir"
        else
            # Ensure existing directories have write permissions
            chmod 777 "$dir"
        fi
    done

    print_success "All necessary directories exist with proper permissions"
}

# Function to wait for apt lock to be released
wait_for_apt_lock() {
    local max_wait=300  # 5 minutes
    local waited=0

    while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || \
          sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1 || \
          sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do

        if [ $waited -ge $max_wait ]; then
            print_error "Timeout waiting for apt lock to be released."
            print_info "Another process (likely unattended-upgrades) is using apt."
            print_info "You can manually stop it with: sudo systemctl stop unattended-upgrades"
            return 1
        fi

        if [ $waited -eq 0 ]; then
            print_info "Waiting for apt lock to be released (another process is using apt)..."
        fi

        sleep 5
        waited=$((waited + 5))

        if [ $((waited % 30)) -eq 0 ]; then
            print_info "Still waiting... ($waited seconds elapsed)"
        fi
    done

    return 0
}

# Function to install Docker Compose
install_docker_compose() {
    print_header "Installing Docker Compose"

    # Check if docker-compose is already installed
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose is already installed"
        docker-compose version | head -1
        return 0
    fi

    # Detect OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        print_error "Cannot detect OS. Please install Docker Compose manually."
        return 1
    fi

    print_info "Detected OS: $OS"

    # Fix any broken apt state first (only for Debian-based)
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        print_info "Fixing any broken package state..."
        sudo apt-get install -f -y 2>/dev/null || true
    fi

    case "$OS" in
        ubuntu|debian)
            # Wait for apt lock if needed
            if ! wait_for_apt_lock; then
                return 1
            fi

            print_info "Updating package list..."
            sudo apt-get update

            print_info "Installing Docker Compose v2..."
            sudo apt-get install -y docker-compose-v2

            # Create symlink for backward compatibility
            print_info "Creating symlink for docker-compose command..."
            if [ -f /usr/libexec/docker/cli-plugins/docker-compose ]; then
                sudo ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
            elif [ -f /usr/lib/docker/cli-plugins/docker-compose ]; then
                sudo ln -sf /usr/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
            fi
            ;;

        rhel|centos|fedora|amzn)
            print_info "Installing Docker Compose..."
            sudo dnf install -y docker-compose-plugin

            # Create symlink
            if [ -f /usr/libexec/docker/cli-plugins/docker-compose ]; then
                sudo ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
            fi
            ;;

        *)
            print_warning "Unsupported OS for automatic installation: $OS"
            print_info "Attempting to download Docker Compose binary..."

            # Download latest Docker Compose binary
            DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
            sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
            ;;
    esac

    # Verify installation
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose installed successfully!"
        docker-compose version
        return 0
    else
        print_error "Docker Compose installation failed."
        return 1
    fi
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_warning "docker-compose is not installed."
        print_info "Attempting to install Docker Compose..."

        if install_docker_compose; then
            print_success "Docker Compose installed successfully!"
        else
            print_error "Failed to install Docker Compose."
            print_error "Please install it manually:"
            print_error "  Ubuntu/Debian: sudo apt-get install docker-compose-v2"
            print_error "  RHEL/CentOS: sudo dnf install docker-compose-plugin"
            exit 1
        fi
    else
        print_success "docker-compose is available"
        docker-compose version | head -1
    fi
}

# Function to generate GPU-enabled docker-compose override
generate_gpu_compose() {
    print_info "Generating GPU-enabled docker-compose override..."

    cat > docker-compose.gpu.yml <<'EOF'
version: '3.8'

services:
  # LLM Service with GPU support
  llm-service:
    build:
      context: ./llm/llm-prompt-generation
      dockerfile: Dockerfile.gpu
    environment:
      - LLM_USE_GPU=true
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Coqui TTS XTTS v2 Server (GPU-accelerated)
  # Model is pre-downloaded by deployment script
  coqui-tts:
    command:
      - "--model_path"
      - "/root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2"
      - "--config_path"
      - "/root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/config.json"
      - "--port"
      - "5002"
      - "--use_cuda"
      - "true"
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Audio Generation Factory with GPU support
  audio-generation-factory:
    build:
      context: ./audio-generation
      dockerfile: Dockerfile.gpu
    environment:
      - USE_GPU=true
      - CUDA_VISIBLE_DEVICES=0
      - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
      - COQUI_TTS_URL=http://coqui-tts:5002
      - TEXT_CHUNKER_VERSION=v2  # v1=spaCy, v2=semantic_text_splitter (recommended)
    depends_on:
      - coqui-tts
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # IOPaint with GPU support
  iopaint:
    build:
      context: ./jobs
      dockerfile: ./watermark-remover/Dockerfile.gpu
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Voice Generator Job with GPU awareness
  job-voice-generator:
    environment:
      - USE_GPU=true

  # MongoDB with GPU environment variable for migrations
  ichat-mongodb:
    environment:
      - USE_GPU=true
EOF

    print_success "GPU docker-compose override created: docker-compose.gpu.yml"
}

# Function to download Coqui TTS model
download_coqui_model() {
    print_header "Downloading Coqui TTS Model"

    local model_dir="./coqui-tts-models/tts_models--multilingual--multi-dataset--xtts_v2"
    local parent_dir="./coqui-tts-models"

    # Check if model already exists
    if [ -f "$model_dir/config.json" ]; then
        print_success "Coqui TTS XTTS-v2 model already exists. Skipping download."
        return 0
    fi

    print_info "Downloading XTTS-v2 model from HuggingFace..."
    print_info "This is a one-time download (~2GB, may take 5-10 minutes)"
    echo ""

    # Create parent directory first
    if [ ! -d "$parent_dir" ]; then
        print_info "Creating directory: $parent_dir"
        mkdir -p "$parent_dir"
        chmod 777 "$parent_dir"
    fi

    # Create model directory
    print_info "Creating directory: $model_dir"
    mkdir -p "$model_dir"
    chmod 777 "$model_dir"

    # Download using Python and huggingface-hub
    print_info "Installing huggingface-hub (if not already installed)..."
    python3 -m pip install -q huggingface-hub 2>/dev/null || pip3 install -q huggingface-hub

    print_info "Downloading model files..."
    print_info "Target directory: $model_dir"

    # Use a temporary Python script to avoid heredoc issues
    cat > /tmp/download_coqui_model.py << 'PYEOF'
from huggingface_hub import snapshot_download
import os
import sys

model_dir = sys.argv[1]
print(f"Downloading to: {model_dir}")

try:
    snapshot_download(
        repo_id='coqui/XTTS-v2',
        local_dir=model_dir,
        local_dir_use_symlinks=False
    )
    print("Model download complete!")
except Exception as e:
    print(f"Error downloading model: {e}")
    sys.exit(1)
PYEOF

    python3 /tmp/download_coqui_model.py "$model_dir"
    local download_status=$?
    rm -f /tmp/download_coqui_model.py

    if [ $download_status -eq 0 ]; then
        print_success "✓ Coqui TTS model downloaded successfully!"
        print_info "Model location: $model_dir"
        # Verify the config file exists
        if [ -f "$model_dir/config.json" ]; then
            print_success "✓ Model config.json verified"
        else
            print_error "✗ Model config.json not found after download"
            return 1
        fi
    else
        print_error "✗ Failed to download Coqui TTS model"
        return 1
    fi

    echo ""
}

# Function to build base Docker images (shared across multiple services)
build_base_images() {
    local build_flag=$1

    print_header "Building Base Docker Images"
    print_info "Pre-building shared base images to avoid redundant downloads..."
    echo ""

    # Determine which base images to build based on GPU flag
    local base_images=()

    if [ "$USE_GPU" = true ]; then
        print_info "GPU mode enabled - building CUDA base images"
        base_images=(
            "pytorch-base-cu118:docker/pytorch-base/Dockerfile.cu118"
            "pytorch-node-base-cu118:docker/pytorch-node-base/Dockerfile.cu118"
        )
    else
        print_info "CPU mode - building CPU base images"
        base_images=(
            "pytorch-base-cpu:docker/pytorch-base/Dockerfile.cpu"
            "pytorch-node-base-cpu:docker/pytorch-node-base/Dockerfile.cpu"
        )
    fi

    # Build each base image
    for image_spec in "${base_images[@]}"; do
        IFS=':' read -r image_name dockerfile_path <<< "$image_spec"

        # Check if image exists and skip if not building
        if [ "$build_flag" != "--build" ]; then
            if docker images | grep -q "$image_name"; then
                print_success "Base image $image_name already exists (use --build to rebuild)"
                continue
            fi
        fi

        print_info "Building base image: ${CYAN}$image_name${NC}"
        print_info "  Dockerfile: $dockerfile_path"

        # Extract directory from dockerfile path
        local dockerfile_dir=$(dirname "$dockerfile_path")
        local dockerfile_name=$(basename "$dockerfile_path")

        # Build the image
        if docker build \
            -t "$image_name" \
            -f "$dockerfile_path" \
            "$dockerfile_dir" 2>&1 | tee "/tmp/build-$image_name.log"; then
            print_success "✓ Built $image_name successfully"
        else
            print_error "✗ Failed to build $image_name"
            print_error "  Check logs: /tmp/build-$image_name.log"
            return 1
        fi
        echo ""
    done

    print_success "All base images built successfully!"
    echo ""

    # Show summary of built images
    print_info "Base images summary:"
    for image_spec in "${base_images[@]}"; do
        IFS=':' read -r image_name dockerfile_path <<< "$image_spec"
        local size=$(docker images "$image_name" --format "{{.Size}}" | head -1)
        print_info "  ${CYAN}$image_name${NC} - Size: $size"
    done
    echo ""
}

# Function to get docker-compose command with appropriate files
get_compose_command() {
    local cmd="docker-compose -f docker-compose.yml"

    if [ "$USE_GPU" = true ]; then
        # Always regenerate GPU override to ensure latest configuration
        generate_gpu_compose >&2
        cmd="$cmd -f docker-compose.gpu.yml"
    fi

    echo "$cmd"
}

# Function to validate service name
validate_service() {
    local service=$1
    local valid=false

    for svc in "${SERVICES[@]}"; do
        if [ "$service" = "$svc" ]; then
            valid=true
            break
        fi
    done

    if [ "$valid" = false ]; then
        print_error "Invalid service name: $service"
        print_info "Available services:"
        for svc in "${SERVICES[@]}"; do
            if is_gpu_service "$svc"; then
                echo -e "  ${CYAN}$svc${NC} ${MAGENTA}(GPU capable)${NC}"
            else
                echo "  $svc"
            fi
        done
        exit 1
    fi
}

# Function to deploy a single service
deploy_service() {
    local service=$1
    local build_flag=$2

    # Validate service name
    validate_service "$service"

    # Get the appropriate docker-compose command
    local compose_cmd=$(get_compose_command)

    # Special handling for coqui-tts: ensure model is downloaded first
    if [ "$service" = "coqui-tts" ]; then
        echo ""
        echo "DEBUG: Service is coqui-tts, calling download_coqui_model..."
        download_coqui_model
        local download_result=$?
        echo "DEBUG: download_coqui_model returned: $download_result"

        # Verify model exists before proceeding
        if [ ! -f "./coqui-tts-models/tts_models--multilingual--multi-dataset--xtts_v2/config.json" ]; then
            print_error "Model download failed or incomplete. Cannot deploy coqui-tts."
            echo "DEBUG: Checking directory contents:"
            ls -la ./coqui-tts-models/ || echo "Directory doesn't exist"
            return 1
        fi
        echo ""
    fi

    # Show GPU status if applicable
    if is_gpu_service "$service" && [ "$USE_GPU" = true ]; then
        print_info "Deploying $service with ${MAGENTA}GPU support${NC}..."
    else
        print_info "Deploying $service..."
    fi

    if [ "$build_flag" = "--build" ]; then
        print_info "Building $service..."
        $compose_cmd build "$service"
        print_info "Deploying $service..."
        $compose_cmd up -d --force-recreate "$service"
    else
        print_info "Deploying $service..."
        $compose_cmd up -d "$service"
    fi

    if [ $? -eq 0 ]; then
        print_success "$service deployed successfully"

        # Show GPU info if applicable
        if is_gpu_service "$service" && [ "$USE_GPU" = true ]; then
            local container_name=$($compose_cmd ps -q "$service" 2>/dev/null | xargs docker inspect --format='{{.Name}}' 2>/dev/null | sed 's/\///')
            if [ -n "$container_name" ]; then
                print_info "Verifying GPU access in $container_name..."
                sleep 2
                docker exec "$container_name" nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | while read gpu; do
                    print_success "  GPU detected: $gpu"
                done || print_warning "  Could not verify GPU access (container may still be starting)"
            fi
        fi
    else
        print_error "Failed to deploy $service"
        return 1
    fi
}

# Function to wait for service to be healthy
wait_for_health() {
    local service=$1
    local max_wait=${2:-60}  # Default 60 seconds
    local elapsed=0
    
    print_info "Waiting for $service to be healthy..."
    
    while [ $elapsed -lt $max_wait ]; do
        local health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "no-health-check")
        local status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null || echo "not-running")
        
        if [ "$health" = "healthy" ]; then
            print_success "$service is healthy"
            return 0
        elif [ "$health" = "no-health-check" ] && [ "$status" = "running" ]; then
            print_warning "$service is running (no health check configured)"
            return 0
        elif [ "$status" != "running" ]; then
            print_error "$service is not running"
            return 1
        fi
        
        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done
    
    echo ""
    print_warning "$service health check timeout (still starting...)"
    return 0
}

# Function to show service status
show_status() {
    print_header "Service Status"
    
    echo -e "${BLUE}Service Name${NC}\t\t\t${BLUE}Status${NC}\t\t${BLUE}Health${NC}\t\t${BLUE}Ports${NC}"
    echo "─────────────────────────────────────────────────────────────────────────────────"
    
    for service in "${SERVICES[@]}"; do
        local container_name=$(docker-compose ps -q "$service" 2>/dev/null | xargs docker inspect --format='{{.Name}}' 2>/dev/null | sed 's/\///')
        
        if [ -z "$container_name" ]; then
            echo -e "$service\t\t${RED}Not Created${NC}"
            continue
        fi
        
        local status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null || echo "unknown")
        local health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-check")
        local ports=$(docker inspect --format='{{range $p, $conf := .NetworkSettings.Ports}}{{if $conf}}{{(index $conf 0).HostPort}}->{{$p}} {{end}}{{end}}' "$container_name" 2>/dev/null || echo "none")
        
        # Color code status
        if [ "$status" = "running" ]; then
            status="${GREEN}running${NC}"
        else
            status="${RED}$status${NC}"
        fi
        
        # Color code health
        if [ "$health" = "healthy" ]; then
            health="${GREEN}healthy${NC}"
        elif [ "$health" = "starting" ]; then
            health="${YELLOW}starting${NC}"
        elif [ "$health" = "unhealthy" ]; then
            health="${RED}unhealthy${NC}"
        else
            health="${YELLOW}no-check${NC}"
        fi
        
        echo -e "$service\t$status\t$health\t$ports"
    done
    
    echo ""
}

# Function to show logs
show_logs() {
    local service=${1:-""}
    local compose_cmd=$(get_compose_command)

    if [ -z "$service" ]; then
        print_header "Showing logs for all news services"
        $compose_cmd logs --tail=50 -f "${SERVICES[@]}"
    else
        validate_service "$service"
        print_header "Showing logs for $service"
        $compose_cmd logs --tail=100 -f "$service"
    fi
}

# Function to stop services
stop_services() {
    local service=${1:-""}
    local compose_cmd=$(get_compose_command)

    if [ -z "$service" ]; then
        print_header "Stopping All News Services"

        # Stop in reverse order
        for ((i=${#SERVICES[@]}-1; i>=0; i--)); do
            local svc="${SERVICES[$i]}"
            print_info "Stopping $svc..."
            $compose_cmd stop "$svc"
            print_success "$svc stopped"
        done
    else
        validate_service "$service"
        print_header "Stopping $service"
        $compose_cmd stop "$service"
        print_success "$service stopped"
    fi
}

# Function to restart services
restart_services() {
    local service=${1:-""}
    local build_flag=$2

    if [ -z "$service" ]; then
        print_header "Restarting All News Services"
        stop_services
        sleep 2
        deploy_all_services "$build_flag"
    else
        validate_service "$service"
        print_header "Restarting $service"
        stop_services "$service"
        sleep 2
        deploy_service "$service" "$build_flag"
    fi
}

# Function to deploy services in parallel (background jobs)
deploy_parallel() {
    local services=("$@")
    local pids=()

    for service in "${services[@]}"; do
        deploy_service "$service" "$build_flag" &
        pids+=($!)
    done

    # Wait for all background jobs to complete
    local failed=0
    for pid in "${pids[@]}"; do
        if ! wait $pid; then
            failed=$((failed + 1))
        fi
    done

    return $failed
}

# Function to deploy all services
deploy_all_services() {
    local build_flag=$1

    if [ "$USE_GPU" = true ]; then
        print_header "Deploying News Services with GPU Support (Parallel Mode)"
    else
        print_header "Deploying News Services (CPU Mode - Parallel Mode)"
    fi

    # Check prerequisites
    check_docker
    check_docker_compose

    # Check GPU if requested
    if [ "$USE_GPU" = true ]; then
        check_gpu
    fi

#    check_env_file

    # Create necessary directories
    create_directories

    # Download Coqui TTS model if using GPU (model is needed for TTS service)
    if [ "$USE_GPU" = true ]; then
        print_info "Checking Coqui TTS model..."
        if ! download_coqui_model; then
            print_error "Failed to download Coqui TTS model. Cannot proceed with GPU deployment."
            print_info "Please check your internet connection and try again."
            exit 1
        fi
    fi

    # Build base Docker images first (if --build flag is set or images don't exist)
    # This ensures PyTorch and other common dependencies are downloaded once and reused
    build_base_images "$build_flag"

    # Deploy services in parallel groups based on dependencies
    print_info "Starting parallel deployment sequence..."
    echo ""

    # Group 1: Foundation services (must deploy first)
    print_header "Group 1: Foundation Services (MongoDB, MinIO)"
    print_info "Deploying MongoDB and MinIO in parallel..."
    deploy_parallel "ichat-mongodb" "minio"
    sleep 5  # Give databases time to initialize

    # Group 2: Core services (depend on MongoDB/MinIO)
    print_header "Group 2: Core Services"
    print_info "Deploying Auth, Template, and Asset services in parallel..."
    deploy_parallel "auth-service" "template-service" "asset-service"
    sleep 3

    # Group 3: AI/ML services (GPU-heavy, deploy in parallel)
    print_header "Group 3: AI/ML Services"
    if [ "$USE_GPU" = true ]; then
        print_info "Deploying LLM and Coqui TTS in parallel (GPU-accelerated)..."
        deploy_parallel "llm-service" "coqui-tts"
        sleep 5  # Give models time to load

        print_info "Deploying Audio Generation Factory..."
        deploy_service "audio-generation-factory" "$build_flag"
        sleep 3
    else
        print_info "Deploying LLM, Coqui TTS, and Audio Generation in parallel (CPU mode)..."
        deploy_parallel "llm-service" "coqui-tts" "audio-generation-factory"
        sleep 5
    fi

    # Group 4: Job services (can run in parallel)
    print_header "Group 4: Job Services"
    print_info "Deploying job services in parallel..."
    deploy_parallel \
        "job-news-fetcher" \
        "job-voice-generator" \
        "job-image-auto-marker" \
        "job-video-generator" \
        "job-export-generator" \
        "job-cleanup"
    sleep 3

    # Group 5: Media processing services
    print_header "Group 5: Media Processing Services"
    print_info "Deploying IOPaint and YouTube Uploader in parallel..."
    deploy_parallel "iopaint" "youtube-uploader"
    sleep 3

    # Group 6: High-level services (depend on everything else)
    print_header "Group 6: High-Level Services"
    print_info "Deploying Inventory Creation Service..."
    deploy_service "inventory-creation-service" "$build_flag"
    sleep 2

    # Group 7: API and Frontend (must be last)
    print_header "Group 7: API & Frontend"
    print_info "Deploying API Server and Frontend in parallel..."
    deploy_parallel "ichat-api" "news-automation-frontend"
    
    # Show final status
    echo ""
    print_header "Deployment Complete!"
    show_status
    
    echo ""
    print_success "All news services deployed successfully!"
    echo ""
    print_info "Service URLs:"
    echo "  • Frontend UI:          http://localhost:3002"
    echo "  • API Server:           http://localhost:8080"
    echo "  • Auth Service:         http://localhost:8098"
    echo "  • Template Service:     http://localhost:5010"
    echo "  • Asset Service:        http://localhost:8099"
    echo "  • MinIO Console:        http://localhost:9001 (admin/minioadmin)"
    echo "  • MinIO API:            http://localhost:9000"
    echo "  • News Fetcher:         http://localhost:8093"
    echo "  • LLM Service:          http://localhost:8083"
    echo "  • Audio Generation:     http://localhost:3000"
    echo "  • Voice Generator:      http://localhost:8094"
    echo "  • Watermark Remover:    http://localhost:8096"
    echo "  • Image Auto-Marker:    http://localhost:8102"
    echo "  • Video Generator:      http://localhost:8095"
    echo "  • Export Generator:     http://localhost:8101"
    echo "  • YouTube Uploader:     http://localhost:8097"
    echo "  • Cleanup Job:          http://localhost:8100"
    echo "  • MongoDB:              mongodb://localhost:27017"
    echo ""
    print_info "Default Admin Credentials:"
    echo "  • Email:    admin@newsautomation.com"
    echo "  • Password: admin123"
    echo ""
    print_info "To view logs: ./deploy-news-services.sh --logs"
    print_info "To check status: ./deploy-news-services.sh --status"
    echo ""
}

# Function to show help
show_help() {
    cat << EOF
${BLUE}═══════════════════════════════════════════════════════════${NC}
${BLUE}  News Services Deployment Script${NC}
${BLUE}═══════════════════════════════════════════════════════════${NC}

This script manages deployment of all news-related services:
  1. MongoDB (database)
  2. MinIO (object storage for assets)
  3. Auth Service (authentication and user management)
  4. Template Service (video templates management)
  5. Asset Service (asset management with MinIO)
  6. News Fetcher Job (fetches news articles)
  7. LLM Service (generates summaries) ${MAGENTA}[GPU capable]${NC}
  8. Coqui TTS Server (XTTS-v2 multilingual TTS) ${MAGENTA}[GPU capable]${NC}
  9. Audio Generation Factory (TTS: Kokoro English + Veena Hindi) ${MAGENTA}[GPU capable]${NC}
  10. Voice Generator Job (generates audio from news)
  11. IOPaint Watermark Remover (removes watermarks from images) ${MAGENTA}[GPU capable]${NC}
  12. Image Auto-Marker Job (automatically marks images as cleaned)
  13. Video Generator Job (creates videos from news + audio)
  14. Export Generator Job (exports videos in different formats)
  15. YouTube Uploader (uploads videos to YouTube)
  16. Cleanup Job (cleans up old files and MongoDB records)
  17. E-commerce Service (manages e-commerce products and video generation)
  18. API Server (serves news data to frontend)
  19. News Automation Frontend (React UI for managing news automation)

${YELLOW}Usage:${NC}
  ./deploy-news-services.sh [options] [service_name]

${YELLOW}Options:${NC}
  --build              Force rebuild of services before deployment
  --gpu                Enable GPU support for compatible services
  --service <name>     Deploy only specific service
  --logs [service]     Show logs (all services or specific service)
  --status             Show status of all services
  --stop [service]     Stop all services or specific service
  --restart [service]  Restart all services or specific service
  --help               Show this help message

${YELLOW}Available Services:${NC}
EOF
    for svc in "${SERVICES[@]}"; do
        if is_gpu_service "$svc"; then
            echo -e "  ${CYAN}$svc${NC} ${MAGENTA}(GPU capable)${NC}"
        else
            echo "  $svc"
        fi
    done

    cat << EOF

${YELLOW}Examples:${NC}
  ${GREEN}# Deploy all services (CPU mode)${NC}
  ./deploy-news-services.sh

  ${GREEN}# Deploy all services with rebuild${NC}
  ./deploy-news-services.sh --build

  ${GREEN}# Deploy all services with GPU support${NC}
  ./deploy-news-services.sh --build --gpu

  ${GREEN}# Deploy only LLM service${NC}
  ./deploy-news-services.sh --service llm-service

  ${GREEN}# Deploy LLM service with GPU and rebuild${NC}
  ./deploy-news-services.sh --service llm-service --gpu --build

  ${GREEN}# Deploy audio generation with GPU${NC}
  ./deploy-news-services.sh --service audio-generation-factory --gpu --build

  ${GREEN}# Check status${NC}
  ./deploy-news-services.sh --status

  ${GREEN}# Show logs for specific service${NC}
  ./deploy-news-services.sh --logs llm-service

  ${GREEN}# Stop specific service${NC}
  ./deploy-news-services.sh --stop audio-generation-factory

  ${GREEN}# Restart specific service with rebuild${NC}
  ./deploy-news-services.sh --restart llm-service --build

EOF
}

# Main script logic
main() {
    local build_flag=""
    local action=""
    local target_service=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build)
                build_flag="--build"
                shift
                ;;
            --gpu)
                USE_GPU=true
                shift
                ;;
            --service)
                if [ -z "${2:-}" ]; then
                    print_error "--service requires a service name"
                    show_help
                    exit 1
                fi
                target_service="$2"
                shift 2
                ;;
            --logs)
                action="logs"
                target_service="${2:-}"
                shift
                if [ -n "$target_service" ] && [[ ! "$target_service" =~ ^-- ]]; then
                    shift
                fi
                ;;
            --status)
                action="status"
                shift
                ;;
            --stop)
                action="stop"
                target_service="${2:-}"
                shift
                if [ -n "$target_service" ] && [[ ! "$target_service" =~ ^-- ]]; then
                    shift
                fi
                ;;
            --restart)
                action="restart"
                target_service="${2:-}"
                shift
                if [ -n "$target_service" ] && [[ ! "$target_service" =~ ^-- ]]; then
                    shift
                fi
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo ""
                show_help
                exit 1
                ;;
        esac
    done

    # Execute action
    case "$action" in
        logs)
            show_logs "$target_service"
            ;;
        status)
            show_status
            ;;
        stop)
            stop_services "$target_service"
            ;;
        restart)
            restart_services "$target_service" "$build_flag"
            ;;
        *)
            # Deploy action
            if [ -n "$target_service" ]; then
                # Deploy single service
                deploy_service "$target_service" "$build_flag"
            else
                # Deploy all services
                deploy_all_services "$build_flag"
            fi
            ;;
    esac
}

# Run main function
main "$@"


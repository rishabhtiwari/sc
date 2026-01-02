#!/bin/bash

################################################################################
# News Services Deployment Script
#
# This script deploys all news-related services in the correct order:
# 1. MongoDB (database)
# 2. Auth Service (authentication and user management)
# 3. Template Service (video templates management)
# 4. News Fetcher Job (fetches news articles)
# 5. LLM Service (generates summaries)
# 6. Audio Generation Factory (TTS models: Kokoro for English, Veena for Hindi)
# 7. Voice Generator Job (generates audio from news)
# 8. IOPaint Watermark Remover (removes watermarks from images)
# 9. Video Generator Job (creates videos from news + audio)
# 10. YouTube Uploader (uploads videos to YouTube)
# 11. Cleanup Job (cleans up old files and MongoDB records)
# 12. E-commerce Service (manages e-commerce products and video generation)
# 13. API Server (serves news data to frontend)
# 14. News Automation Frontend (React UI for managing news automation)
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
    "audio-generation-factory"
    "job-voice-generator"
    "iopaint"
    "job-video-generator"
    "youtube-uploader"
    "job-cleanup"
    "inventory-creation-service"
    "ichat-api"
    "news-automation-frontend"
)

# GPU-capable services
GPU_SERVICES=(
    "llm-service"
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

# Function to check GPU availability
check_gpu() {
    if [ "$USE_GPU" = true ]; then
        print_info "Checking GPU availability..."

        # Check if nvidia-smi is available
        if ! command -v nvidia-smi &> /dev/null; then
            print_warning "nvidia-smi not found. GPU support may not work."
            print_warning "Install NVIDIA drivers and CUDA toolkit for GPU support."
            return 1
        fi

        # Check if NVIDIA Docker runtime is available
        if ! docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
            print_warning "NVIDIA Docker runtime not available."
            print_warning "Install nvidia-docker2 for GPU support in containers."
            return 1
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
        "jobs/youtube-uploader/logs"
        "jobs/youtube-uploader/credentials"
        "jobs/cleanup/logs"
        "jobs/watermark-remover/public"
        "jobs/watermark-remover/models"
        "audio-generation/data"
        "audio-generation/public"
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

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
    print_success "docker-compose is available"
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

  # Audio Generation Factory with GPU support
  audio-generation-factory:
    build:
      context: ./audio-generation
      dockerfile: Dockerfile.gpu
    environment:
      - USE_GPU=true
      - CUDA_VISIBLE_DEVICES=0
      - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
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
EOF

    print_success "GPU docker-compose override created: docker-compose.gpu.yml"
}

# Function to get docker-compose command with appropriate files
get_compose_command() {
    local cmd="docker-compose -f docker-compose.yml"

    if [ "$USE_GPU" = true ]; then
        # Generate GPU override if it doesn't exist
        if [ ! -f "docker-compose.gpu.yml" ]; then
            generate_gpu_compose >&2
        fi
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

    # Show GPU status if applicable
    if is_gpu_service "$service" && [ "$USE_GPU" = true ]; then
        print_info "Deploying $service with ${MAGENTA}GPU support${NC}..."
    else
        print_info "Deploying $service..."
    fi

    if [ "$build_flag" = "--build" ]; then
        print_info "Building and deploying $service..."
        $compose_cmd up -d --build "$service"
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

# Function to deploy all services
deploy_all_services() {
    local build_flag=$1

    if [ "$USE_GPU" = true ]; then
        print_header "Deploying News Services with GPU Support"
    else
        print_header "Deploying News Services (CPU Mode)"
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

    # Deploy services in order
    print_info "Starting deployment sequence..."
    echo ""
    
    # 1. MongoDB
    print_header "Step 1/16: MongoDB Database"
    deploy_service "ichat-mongodb" "$build_flag"
    # wait_for_health "ichat-mongodb" 60

    # 2. MinIO Object Storage
    print_header "Step 2/16: MinIO Object Storage"
    deploy_service "minio" "$build_flag"
    # wait_for_health "ichat-minio" 60

    # 3. Auth Service
    print_header "Step 3/16: Auth Service (Authentication & User Management)"
    deploy_service "auth-service" "$build_flag"
    # wait_for_health "ichat-auth-service" 60

    # 4. Template Service
    print_header "Step 4/16: Template Service (Video Templates)"
    deploy_service "template-service" "$build_flag"
    # wait_for_health "ichat-template-service" 60

    # 5. Asset Service
    print_header "Step 5/16: Asset Service (Asset Management with MinIO)"
    deploy_service "asset-service" "$build_flag"
    # wait_for_health "ichat-asset-service" 60

    # 6. News Fetcher
    print_header "Step 6/16: News Fetcher Job"
    deploy_service "job-news-fetcher" "$build_flag"
    # wait_for_health "ichat-news-fetcher" 60

    # 7. LLM Service
    print_header "Step 7/16: LLM Service"
    deploy_service "llm-service" "$build_flag"
    # wait_for_health "ichat-llm-service" 180  # LLM takes longer to load model

    # 8. Audio Generation Factory
    print_header "Step 8/16: Audio Generation Factory (Kokoro + Veena TTS)"
    deploy_service "audio-generation-factory" "$build_flag"
    # wait_for_health "audio-generation-factory" 180  # TTS models take time to load

    # 9. Voice Generator Job
    print_header "Step 9/16: Voice Generator Job"
    deploy_service "job-voice-generator" "$build_flag"
    # wait_for_health "ichat-voice-generator" 60

    # 10. IOPaint Watermark Remover
    print_header "Step 10/16: IOPaint Watermark Remover"
    deploy_service "iopaint" "$build_flag"
    # wait_for_health "ichat-iopaint" 60

    # 11. Video Generator Job
    print_header "Step 11/16: Video Generator Job"
    deploy_service "job-video-generator" "$build_flag"
    # wait_for_health "ichat-video-generator" 60

    # 12. YouTube Uploader
    print_header "Step 12/16: YouTube Uploader"
    deploy_service "youtube-uploader" "$build_flag"
    # wait_for_health "ichat-youtube-uploader" 60

    # 13. Cleanup Job
    print_header "Step 13/16: Cleanup Job"
    deploy_service "job-cleanup" "$build_flag"
    # wait_for_health "ichat-cleanup" 60

    # 14. Inventory Creation Service
    print_header "Step 14/16: Inventory Creation Service (Generic Content Generation)"
    deploy_service "inventory-creation-service" "$build_flag"
    # wait_for_health "ichat-inventory-creation-service" 60

    # 15. API Server
    print_header "Step 15/16: API Server"
    deploy_service "ichat-api" "$build_flag"
    # wait_for_health "ichat-api-server" 60

    # 16. News Automation Frontend
    print_header "Step 16/16: News Automation Frontend"
    deploy_service "news-automation-frontend" "$build_flag"
    # wait_for_health "news-automation-frontend" 60
    
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
    echo "  • Video Generator:      http://localhost:8095"
    echo "  • YouTube Uploader:     http://localhost:8097"
    echo "  • Cleanup Job:          http://localhost:8100"
    echo "  • E-commerce Service:   http://localhost:8101"
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
  8. Audio Generation Factory (TTS: Kokoro English + Veena Hindi) ${MAGENTA}[GPU capable]${NC}
  9. Voice Generator Job (generates audio from news)
  10. IOPaint Watermark Remover (removes watermarks from images) ${MAGENTA}[GPU capable]${NC}
  11. Video Generator Job (creates videos from news + audio)
  12. YouTube Uploader (uploads videos to YouTube)
  13. Cleanup Job (cleans up old files and MongoDB records)
  14. E-commerce Service (manages e-commerce products and video generation)
  15. API Server (serves news data to frontend)
  16. News Automation Frontend (React UI for managing news automation)

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


#!/bin/bash

################################################################################
# News Services Deployment Script
# 
# This script deploys all news-related services in the correct order:
# 1. MongoDB (database)
# 2. News Fetcher Job (fetches news articles)
# 3. LLM Service (generates summaries)
# 4. Audio Generation Factory (TTS models: Kokoro for English, Veena for Hindi)
# 5. Voice Generator Job (generates audio from news)
# 6. Video Generator Job (creates videos from news + audio)
# 7. API Server (serves news data to frontend)
#
# Usage:
#   ./deploy-news-services.sh [options]
#
# Options:
#   --build         Force rebuild of all services
#   --logs          Show logs after deployment
#   --status        Show status of all services
#   --stop          Stop all news services
#   --restart       Restart all news services
#   --help          Show this help message
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service names
SERVICES=(
    "ichat-mongodb"
    "job-news-fetcher"
    "llm-service"
    "audio-generation-factory"
    "job-voice-generator"
    "job-video-generator"
    "ichat-api"
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

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
    print_success "docker-compose is available"
}

# Function to deploy a single service
deploy_service() {
    local service=$1
    local build_flag=$2
    
    print_info "Deploying $service..."
    
    if [ "$build_flag" = "--build" ]; then
        docker-compose build "$service"
    fi
    
    docker-compose up -d "$service"
    
    if [ $? -eq 0 ]; then
        print_success "$service deployed successfully"
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
    
    if [ -z "$service" ]; then
        print_header "Showing logs for all news services"
        docker-compose logs --tail=50 -f "${SERVICES[@]}"
    else
        print_header "Showing logs for $service"
        docker-compose logs --tail=100 -f "$service"
    fi
}

# Function to stop all services
stop_services() {
    print_header "Stopping News Services"
    
    # Stop in reverse order
    for ((i=${#SERVICES[@]}-1; i>=0; i--)); do
        local service="${SERVICES[$i]}"
        print_info "Stopping $service..."
        docker-compose stop "$service"
        print_success "$service stopped"
    done
}

# Function to restart all services
restart_services() {
    print_header "Restarting News Services"
    
    stop_services
    sleep 2
    deploy_all_services "$1"
}

# Function to deploy all services
deploy_all_services() {
    local build_flag=$1
    
    print_header "Deploying News Services"
    
    # Check prerequisites
    check_docker
    check_docker_compose
    
    # Deploy services in order
    print_info "Starting deployment sequence..."
    echo ""
    
    # 1. MongoDB
    print_header "Step 1/7: MongoDB Database"
    deploy_service "ichat-mongodb" "$build_flag"
    wait_for_health "ichat-mongodb" 60
    
    # 2. News Fetcher
    print_header "Step 2/7: News Fetcher Job"
    deploy_service "job-news-fetcher" "$build_flag"
    wait_for_health "ichat-news-fetcher" 60
    
    # 3. LLM Service
    print_header "Step 3/7: LLM Service"
    deploy_service "llm-service" "$build_flag"
    wait_for_health "ichat-llm-service" 180  # LLM takes longer to load model
    
    # 4. Audio Generation Factory
    print_header "Step 4/7: Audio Generation Factory (Kokoro + Veena TTS)"
    deploy_service "audio-generation-factory" "$build_flag"
    wait_for_health "audio-generation-factory" 180  # TTS models take time to load
    
    # 5. Voice Generator Job
    print_header "Step 5/7: Voice Generator Job"
    deploy_service "job-voice-generator" "$build_flag"
    wait_for_health "ichat-voice-generator" 60
    
    # 6. Video Generator Job
    print_header "Step 6/7: Video Generator Job"
    deploy_service "job-video-generator" "$build_flag"
    wait_for_health "ichat-video-generator" 60
    
    # 7. API Server
    print_header "Step 7/7: API Server"
    deploy_service "ichat-api" "$build_flag"
    wait_for_health "ichat-api-server" 60
    
    # Show final status
    echo ""
    print_header "Deployment Complete!"
    show_status
    
    echo ""
    print_success "All news services deployed successfully!"
    echo ""
    print_info "Service URLs:"
    echo "  • API Server:           http://localhost:8080"
    echo "  • News Fetcher:         http://localhost:8093"
    echo "  • LLM Service:          http://localhost:8083"
    echo "  • Audio Generation:     http://localhost:3000"
    echo "  • Voice Generator:      http://localhost:8094"
    echo "  • Video Generator:      http://localhost:8095"
    echo "  • MongoDB:              mongodb://localhost:27017"
    echo ""
    print_info "To view logs: ./deploy-news-services.sh --logs"
    print_info "To check status: ./deploy-news-services.sh --status"
    echo ""
}

# Function to show help
show_help() {
    cat << EOF
News Services Deployment Script

This script manages deployment of all news-related services:
  1. MongoDB (database)
  2. News Fetcher Job (fetches news articles)
  3. LLM Service (generates summaries)
  4. Audio Generation Factory (TTS: Kokoro English + Veena Hindi)
  5. Voice Generator Job (generates audio from news)
  6. Video Generator Job (creates videos from news + audio)
  7. API Server (serves news data to frontend)

Usage:
  ./deploy-news-services.sh [options]

Options:
  --build         Force rebuild of all services before deployment
  --logs [svc]    Show logs (optionally for specific service)
  --status        Show status of all services
  --stop          Stop all news services
  --restart       Restart all news services
  --help          Show this help message

Examples:
  # Deploy all services
  ./deploy-news-services.sh

  # Deploy with rebuild
  ./deploy-news-services.sh --build

  # Check status
  ./deploy-news-services.sh --status

  # View logs for all services
  ./deploy-news-services.sh --logs

  # View logs for specific service
  ./deploy-news-services.sh --logs job-news-fetcher

  # Restart all services
  ./deploy-news-services.sh --restart

  # Stop all services
  ./deploy-news-services.sh --stop

EOF
}

# Main script logic
main() {
    case "${1:-}" in
        --build)
            deploy_all_services "--build"
            ;;
        --logs)
            show_logs "${2:-}"
            ;;
        --status)
            show_status
            ;;
        --stop)
            stop_services
            ;;
        --restart)
            restart_services "${2:-}"
            ;;
        --help|-h)
            show_help
            ;;
        "")
            deploy_all_services ""
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


#!/bin/bash

# OCR Service Docker Management Script
# Provides easy commands to manage the OCR service container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="ichat-ocr-service"
IMAGE_NAME="ichat-ocr-service"
PORT="8081"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[OCR Service]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Function to check if container exists
container_exists() {
    docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"
}

# Function to check if container is running
container_running() {
    docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"
}

# Function to build the Docker image
build_image() {
    print_status "Building OCR service Docker image..."
    
    if docker build -t $IMAGE_NAME .; then
        print_success "OCR service image built successfully"
    else
        print_error "Failed to build OCR service image"
        exit 1
    fi
}

# Function to run the container
run_container() {
    print_status "Starting OCR service container..."
    
    # Stop existing container if running
    if container_running; then
        print_warning "Stopping existing container..."
        docker stop $CONTAINER_NAME >/dev/null 2>&1
    fi
    
    # Remove existing container if exists
    if container_exists; then
        print_warning "Removing existing container..."
        docker rm $CONTAINER_NAME >/dev/null 2>&1
    fi
    
    # Create directories for volumes
    mkdir -p uploads outputs logs
    
    # Run new container
    if docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:$PORT \
        -v "$(pwd)/uploads:/app/uploads" \
        -v "$(pwd)/outputs:/app/outputs" \
        -v "$(pwd)/logs:/app/logs" \
        -e FLASK_ENV=production \
        -e FLASK_DEBUG=false \
        $IMAGE_NAME; then
        
        print_success "OCR service container started"
        print_status "Container: $CONTAINER_NAME"
        print_status "Port: http://localhost:$PORT"
        print_status "Health check: http://localhost:$PORT/health"
        
        # Wait a moment and check health
        sleep 3
        check_health
    else
        print_error "Failed to start OCR service container"
        exit 1
    fi
}

# Function to stop the container
stop_container() {
    if container_running; then
        print_status "Stopping OCR service container..."
        docker stop $CONTAINER_NAME
        print_success "OCR service container stopped"
    else
        print_warning "OCR service container is not running"
    fi
}

# Function to restart the container
restart_container() {
    print_status "Restarting OCR service container..."
    stop_container
    sleep 2
    
    if container_exists; then
        docker start $CONTAINER_NAME
        print_success "OCR service container restarted"
        sleep 3
        check_health
    else
        print_error "Container does not exist. Use 'run' command first."
    fi
}

# Function to show container logs
show_logs() {
    if container_exists; then
        print_status "Showing OCR service logs (Ctrl+C to exit)..."
        docker logs -f $CONTAINER_NAME
    else
        print_error "OCR service container does not exist"
    fi
}

# Function to open shell in container
open_shell() {
    if container_running; then
        print_status "Opening shell in OCR service container..."
        docker exec -it $CONTAINER_NAME /bin/bash
    else
        print_error "OCR service container is not running"
    fi
}

# Function to check health
check_health() {
    print_status "Checking OCR service health..."
    
    if curl -s http://localhost:$PORT/health >/dev/null 2>&1; then
        print_success "OCR service is healthy and responding"
        
        # Show service info
        echo ""
        curl -s http://localhost:$PORT/health | python3 -m json.tool 2>/dev/null || echo "Health check passed"
    else
        print_warning "OCR service health check failed"
        print_status "Container may still be starting up..."
    fi
}

# Function to show container status
show_status() {
    print_status "OCR Service Status:"
    echo ""
    
    if container_exists; then
        docker ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        if container_running; then
            check_health
        else
            print_warning "Container exists but is not running"
        fi
    else
        print_warning "OCR service container does not exist"
        echo "Use './docker-run.sh build && ./docker-run.sh run' to create and start"
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up OCR service resources..."
    
    # Stop and remove container
    if container_running; then
        docker stop $CONTAINER_NAME >/dev/null 2>&1
    fi
    
    if container_exists; then
        docker rm $CONTAINER_NAME >/dev/null 2>&1
    fi
    
    # Remove image
    if docker images -q $IMAGE_NAME >/dev/null 2>&1; then
        docker rmi $IMAGE_NAME >/dev/null 2>&1
    fi
    
    print_success "OCR service cleanup completed"
}

# Function to show usage
show_usage() {
    echo -e "${PURPLE}OCR Service Docker Management${NC}"
    echo "================================"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  build     - Build the OCR service Docker image"
    echo "  run       - Run the OCR service container"
    echo "  stop      - Stop the OCR service container"
    echo "  restart   - Restart the OCR service container"
    echo "  logs      - Show container logs (follow mode)"
    echo "  shell     - Open shell in running container"
    echo "  health    - Check service health"
    echo "  status    - Show container status"
    echo "  clean     - Clean up all resources"
    echo ""
    echo "Examples:"
    echo "  $0 build && $0 run    # Build and run"
    echo "  $0 health             # Check if service is healthy"
    echo "  $0 logs               # Follow logs"
}

# Main script logic
case "${1:-}" in
    "build")
        build_image
        ;;
    "run")
        run_container
        ;;
    "stop")
        stop_container
        ;;
    "restart")
        restart_container
        ;;
    "logs")
        show_logs
        ;;
    "shell")
        open_shell
        ;;
    "health")
        check_health
        ;;
    "status")
        show_status
        ;;
    "clean")
        cleanup
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

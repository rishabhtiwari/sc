#!/bin/bash

# iChat Services Management Script
# Manages both API server and OCR service containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${PURPLE}🚀 iChat Services Manager${NC}"
    echo "=================================="
}

print_status() {
    echo -e "${BLUE}[Services]${NC} $1"
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

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to start all services
start_services() {
    print_header
    print_status "Starting iChat services..."
    
    check_docker
    
    # Build and start services with Docker Compose
    print_status "Building and starting containers..."
    if docker-compose up -d --build; then
        print_success "All services started successfully"
        
        # Wait for services to be ready
        print_status "Waiting for services to be ready..."
        sleep 10
        
        # Check service health
        check_all_health
        
        # Show service URLs
        show_service_info
    else
        print_error "Failed to start services"
        exit 1
    fi
}

# Function to stop all services
stop_services() {
    print_header
    print_status "Stopping iChat services..."
    
    if docker-compose down; then
        print_success "All services stopped"
    else
        print_error "Failed to stop services"
        exit 1
    fi
}

# Function to restart all services
restart_services() {
    print_header
    print_status "Restarting iChat services..."
    
    stop_services
    sleep 3
    start_services
}

# Function to check health of all services
check_all_health() {
    print_status "Checking service health..."
    
    # Check API Server
    if curl -s http://localhost:8080/api/health >/dev/null 2>&1; then
        print_success "API Server (port 8080) is healthy"
    else
        print_warning "API Server (port 8080) health check failed"
    fi
    
    # Check OCR Service
    if curl -s http://localhost:8081/health >/dev/null 2>&1; then
        print_success "OCR Service (port 8081) is healthy"
    else
        print_warning "OCR Service (port 8081) health check failed"
    fi
}

# Function to show service information
show_service_info() {
    echo ""
    print_status "🌐 Service URLs:"
    echo "  📡 API Server:     http://localhost:8080"
    echo "  📄 OCR Service:    http://localhost:8081"
    echo ""
    print_status "🔍 Health Checks:"
    echo "  📡 API Health:     http://localhost:8080/api/health"
    echo "  📄 OCR Health:     http://localhost:8081/health"
    echo ""
    print_status "📚 API Documentation:"
    echo "  📡 API Endpoints:  http://localhost:8080/api"
    echo "  📄 OCR Endpoints:  http://localhost:8081"
    echo ""
}

# Function to show logs
show_logs() {
    print_header
    print_status "Showing service logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

# Function to show status
show_status() {
    print_header
    print_status "Service Status:"
    echo ""
    
    # Show container status
    docker-compose ps
    echo ""
    
    # Check health
    check_all_health
    
    # Show service info
    show_service_info
}

# Function to run development mode
dev_mode() {
    print_header
    print_status "Starting services in development mode..."
    
    check_docker
    
    # Start with live reload and debug
    FLASK_ENV=development FLASK_DEBUG=true docker-compose up --build
}

# Function to clean up everything
cleanup() {
    print_header
    print_status "Cleaning up all iChat resources..."
    
    # Stop and remove containers
    docker-compose down --volumes --remove-orphans
    
    # Remove images
    docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Function to test services
test_services() {
    print_header
    print_status "Testing iChat services..."
    
    echo ""
    print_status "Testing API Server..."
    
    # Test API server
    if curl -s http://localhost:8080/api/health | grep -q "healthy"; then
        print_success "API Server test passed"
        
        # Test chat endpoint
        response=$(curl -s -X POST http://localhost:8080/api/chat \
            -H "Content-Type: application/json" \
            -d '{"message": "Hello from test!", "client": "test"}')
        
        if echo "$response" | grep -q "message"; then
            print_success "Chat endpoint test passed"
        else
            print_warning "Chat endpoint test failed"
        fi
    else
        print_error "API Server test failed"
    fi
    
    echo ""
    print_status "Testing OCR Service..."
    
    # Test OCR service
    if curl -s http://localhost:8081/health | grep -q "healthy"; then
        print_success "OCR Service test passed"
        
        # Test formats endpoint
        if curl -s http://localhost:8081/formats | grep -q "supported_formats"; then
            print_success "OCR formats endpoint test passed"
        else
            print_warning "OCR formats endpoint test failed"
        fi
    else
        print_error "OCR Service test failed"
    fi
    
    echo ""
    print_success "Service testing completed"
}

# Function to show usage
show_usage() {
    print_header
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services (API + OCR)"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Show service status and health"
    echo "  logs      - Show service logs (follow mode)"
    echo "  test      - Test all service endpoints"
    echo "  dev       - Start in development mode"
    echo "  clean     - Clean up all resources"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start all services"
    echo "  $0 status             # Check service status"
    echo "  $0 test               # Test all endpoints"
    echo "  $0 logs               # Follow service logs"
}

# Main script logic
case "${1:-}" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "test")
        test_services
        ;;
    "dev")
        dev_mode
        ;;
    "clean")
        cleanup
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

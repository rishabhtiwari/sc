#!/bin/bash
# ============================================
# Frontend Deployment Script
# ============================================
# Deploys the News Automation Frontend with:
# - Pre-deployment checks
# - Backup creation
# - Rolling deployment
# - Health checks
# - Rollback capability
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"
DEPLOYMENT_LOG="$PROJECT_ROOT/logs/deployment.log"
SERVICE_NAME="news-automation-frontend"
CONTAINER_NAME="news-automation-frontend"
HEALTH_CHECK_URL="http://localhost:3002/health"
MAX_HEALTH_CHECK_ATTEMPTS=30
HEALTH_CHECK_INTERVAL=2

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$DEPLOYMENT_LOG")"

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$DEPLOYMENT_LOG"
}

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Print section header
print_header() {
    echo ""
    print_message "$BLUE" "=========================================="
    print_message "$BLUE" "$1"
    print_message "$BLUE" "=========================================="
}

# Check if Docker is running
check_docker() {
    print_header "Checking Docker"
    if ! docker info > /dev/null 2>&1; then
        print_message "$RED" "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_message "$GREEN" "✅ Docker is running"
    log "INFO" "Docker check passed"
}

# Check if docker-compose is available
check_docker_compose() {
    print_header "Checking Docker Compose"
    if ! command -v docker-compose &> /dev/null; then
        print_message "$RED" "❌ docker-compose is not installed"
        exit 1
    fi
    print_message "$GREEN" "✅ Docker Compose is available"
    log "INFO" "Docker Compose check passed"
}

# Create backup of current deployment
create_backup() {
    print_header "Creating Backup"
    
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_name="frontend_backup_${backup_timestamp}"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Check if container exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_message "$YELLOW" "📦 Creating backup of current container..."
        
        # Export container
        docker export "$CONTAINER_NAME" > "$backup_path/container.tar" 2>/dev/null || true
        
        # Save container logs
        docker logs "$CONTAINER_NAME" > "$backup_path/container.log" 2>&1 || true
        
        # Save container inspect
        docker inspect "$CONTAINER_NAME" > "$backup_path/container-inspect.json" 2>/dev/null || true
        
        print_message "$GREEN" "✅ Backup created: $backup_name"
        log "INFO" "Backup created at $backup_path"
        
        # Save backup path for potential rollback
        echo "$backup_path" > "$BACKUP_DIR/latest_backup.txt"
    else
        print_message "$YELLOW" "⚠️  No existing container found, skipping backup"
        log "WARN" "No existing container to backup"
    fi
}

# Build the frontend image
build_image() {
    print_header "Building Frontend Image"
    
    cd "$PROJECT_ROOT"
    
    print_message "$YELLOW" "🔨 Building Docker image..."
    log "INFO" "Starting image build"
    
    if docker-compose build "$SERVICE_NAME"; then
        print_message "$GREEN" "✅ Image built successfully"
        log "INFO" "Image build completed"
    else
        print_message "$RED" "❌ Image build failed"
        log "ERROR" "Image build failed"
        exit 1
    fi
}

# Stop the current container
stop_container() {
    print_header "Stopping Current Container"
    
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_message "$YELLOW" "🛑 Stopping container..."
        docker-compose stop "$SERVICE_NAME"
        print_message "$GREEN" "✅ Container stopped"
        log "INFO" "Container stopped"
    else
        print_message "$YELLOW" "⚠️  Container not running"
        log "WARN" "Container was not running"
    fi
}

# Start the new container
start_container() {
    print_header "Starting New Container"
    
    print_message "$YELLOW" "🚀 Starting container..."
    log "INFO" "Starting container"
    
    cd "$PROJECT_ROOT"
    
    if docker-compose up -d "$SERVICE_NAME"; then
        print_message "$GREEN" "✅ Container started"
        log "INFO" "Container started successfully"
    else
        print_message "$RED" "❌ Failed to start container"
        log "ERROR" "Container start failed"
        exit 1
    fi
}

# Health check
health_check() {
    print_header "Running Health Checks"
    
    print_message "$YELLOW" "🏥 Waiting for service to be healthy..."
    log "INFO" "Starting health checks"
    
    local attempt=1
    while [ $attempt -le $MAX_HEALTH_CHECK_ATTEMPTS ]; do
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            print_message "$GREEN" "✅ Health check passed (attempt $attempt/$MAX_HEALTH_CHECK_ATTEMPTS)"
            log "INFO" "Health check passed"
            return 0
        fi
        
        print_message "$YELLOW" "⏳ Health check attempt $attempt/$MAX_HEALTH_CHECK_ATTEMPTS..."
        sleep $HEALTH_CHECK_INTERVAL
        attempt=$((attempt + 1))
    done
    
    print_message "$RED" "❌ Health check failed after $MAX_HEALTH_CHECK_ATTEMPTS attempts"
    log "ERROR" "Health check failed"
    return 1
}

# Cleanup old images
cleanup() {
    print_header "Cleanup"
    
    print_message "$YELLOW" "🧹 Removing dangling images..."
    docker image prune -f > /dev/null 2>&1 || true
    
    print_message "$GREEN" "✅ Cleanup completed"
    log "INFO" "Cleanup completed"
}

# Main deployment function
deploy() {
    print_header "Starting Frontend Deployment"
    log "INFO" "Deployment started"
    
    # Pre-deployment checks
    check_docker
    check_docker_compose
    
    # Create backup
    create_backup
    
    # Build new image
    build_image
    
    # Stop current container
    stop_container
    
    # Start new container
    start_container
    
    # Health check
    if health_check; then
        print_header "Deployment Successful"
        print_message "$GREEN" "✅ Frontend deployed successfully!"
        print_message "$GREEN" "🌐 Frontend is available at: http://localhost:3002"
        log "INFO" "Deployment completed successfully"
        
        # Cleanup
        cleanup
        
        # Show container status
        echo ""
        print_message "$BLUE" "Container Status:"
        docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        return 0
    else
        print_header "Deployment Failed"
        print_message "$RED" "❌ Deployment failed - health check did not pass"
        print_message "$YELLOW" "💡 Run './scripts/rollback-frontend.sh' to rollback to previous version"
        log "ERROR" "Deployment failed - health check did not pass"
        
        # Show logs
        echo ""
        print_message "$YELLOW" "Recent logs:"
        docker logs --tail 50 "$CONTAINER_NAME"
        
        return 1
    fi
}

# Run deployment
deploy

exit $?


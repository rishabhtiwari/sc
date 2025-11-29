#!/bin/bash
# ============================================
# Frontend Rollback Script
# ============================================
# Rolls back the frontend to the previous backup
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
ROLLBACK_LOG="$PROJECT_ROOT/logs/rollback.log"
SERVICE_NAME="news-automation-frontend"
CONTAINER_NAME="news-automation-frontend"
HEALTH_CHECK_URL="http://localhost:3002/health"
MAX_HEALTH_CHECK_ATTEMPTS=30
HEALTH_CHECK_INTERVAL=2

# Create necessary directories
mkdir -p "$(dirname "$ROLLBACK_LOG")"

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$ROLLBACK_LOG"
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

# List available backups
list_backups() {
    print_header "Available Backups"
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
        print_message "$RED" "❌ No backups found in $BACKUP_DIR"
        exit 1
    fi
    
    local backups=($(ls -dt "$BACKUP_DIR"/frontend_backup_* 2>/dev/null))
    
    if [ ${#backups[@]} -eq 0 ]; then
        print_message "$RED" "❌ No frontend backups found"
        exit 1
    fi
    
    echo "Available backups:"
    local i=1
    for backup in "${backups[@]}"; do
        local backup_name=$(basename "$backup")
        local backup_date=$(echo "$backup_name" | sed 's/frontend_backup_//' | sed 's/_/ /')
        echo "  $i) $backup_name (Created: $backup_date)"
        i=$((i + 1))
    done
    
    echo "${backups[@]}"
}

# Get latest backup
get_latest_backup() {
    if [ -f "$BACKUP_DIR/latest_backup.txt" ]; then
        cat "$BACKUP_DIR/latest_backup.txt"
    else
        local backups=($(ls -dt "$BACKUP_DIR"/frontend_backup_* 2>/dev/null))
        if [ ${#backups[@]} -gt 0 ]; then
            echo "${backups[0]}"
        else
            echo ""
        fi
    fi
}

# Stop current container
stop_container() {
    print_header "Stopping Current Container"
    
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_message "$YELLOW" "🛑 Stopping container..."
        docker stop "$CONTAINER_NAME" > /dev/null 2>&1
        print_message "$GREEN" "✅ Container stopped"
        log "INFO" "Container stopped"
    else
        print_message "$YELLOW" "⚠️  Container not running"
        log "WARN" "Container was not running"
    fi
}

# Remove current container
remove_container() {
    print_header "Removing Current Container"
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_message "$YELLOW" "🗑️  Removing container..."
        docker rm "$CONTAINER_NAME" > /dev/null 2>&1
        print_message "$GREEN" "✅ Container removed"
        log "INFO" "Container removed"
    else
        print_message "$YELLOW" "⚠️  Container does not exist"
        log "WARN" "Container did not exist"
    fi
}

# Restore from backup
restore_backup() {
    local backup_path=$1
    
    print_header "Restoring from Backup"
    print_message "$YELLOW" "📦 Restoring from: $(basename "$backup_path")"
    log "INFO" "Restoring from backup: $backup_path"
    
    if [ ! -f "$backup_path/container.tar" ]; then
        print_message "$RED" "❌ Backup file not found: $backup_path/container.tar"
        log "ERROR" "Backup file not found"
        exit 1
    fi
    
    # Import container from backup
    print_message "$YELLOW" "📥 Importing container from backup..."
    cat "$backup_path/container.tar" | docker import - "frontend-backup:latest" > /dev/null
    
    print_message "$GREEN" "✅ Backup imported"
    log "INFO" "Backup imported successfully"
}

# Start container from backup
start_from_backup() {
    print_header "Starting Container from Backup"
    
    print_message "$YELLOW" "🚀 Starting container from backup image..."
    log "INFO" "Starting container from backup"
    
    # Use docker-compose to start with proper configuration
    cd "$PROJECT_ROOT"
    docker-compose up -d "$SERVICE_NAME"
    
    print_message "$GREEN" "✅ Container started"
    log "INFO" "Container started from backup"
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

# Main rollback function
rollback() {
    print_header "Starting Frontend Rollback"
    log "INFO" "Rollback started"
    
    # Get latest backup
    local backup_path=$(get_latest_backup)
    
    if [ -z "$backup_path" ] || [ ! -d "$backup_path" ]; then
        print_message "$RED" "❌ No backup found to rollback to"
        log "ERROR" "No backup found"
        
        # List available backups
        local backups_output=$(list_backups)
        
        exit 1
    fi
    
    print_message "$YELLOW" "📋 Rolling back to: $(basename "$backup_path")"
    
    # Confirm rollback
    read -p "Are you sure you want to rollback? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_message "$YELLOW" "⚠️  Rollback cancelled"
        log "INFO" "Rollback cancelled by user"
        exit 0
    fi
    
    # Stop current container
    stop_container
    
    # Remove current container
    remove_container
    
    # Restore from backup (or rebuild from source)
    # Note: Since we're using docker-compose, we'll rebuild from source
    # The backup is mainly for reference and logs
    print_header "Rebuilding from Source"
    print_message "$YELLOW" "🔨 Rebuilding frontend from source..."
    cd "$PROJECT_ROOT"
    docker-compose build "$SERVICE_NAME"
    
    # Start container
    start_from_backup
    
    # Health check
    if health_check; then
        print_header "Rollback Successful"
        print_message "$GREEN" "✅ Frontend rolled back successfully!"
        print_message "$GREEN" "🌐 Frontend is available at: http://localhost:3002"
        log "INFO" "Rollback completed successfully"
        
        # Show container status
        echo ""
        print_message "$BLUE" "Container Status:"
        docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        return 0
    else
        print_header "Rollback Failed"
        print_message "$RED" "❌ Rollback failed - health check did not pass"
        log "ERROR" "Rollback failed - health check did not pass"
        
        # Show logs
        echo ""
        print_message "$YELLOW" "Recent logs:"
        docker logs --tail 50 "$CONTAINER_NAME"
        
        return 1
    fi
}

# Run rollback
rollback

exit $?


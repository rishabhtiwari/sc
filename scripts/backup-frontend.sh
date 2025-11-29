#!/bin/bash
# ============================================
# Frontend Backup Script
# ============================================
# Creates a backup of the frontend deployment
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
BACKUP_LOG="$PROJECT_ROOT/logs/backup.log"
CONTAINER_NAME="news-automation-frontend"
MAX_BACKUPS=10

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$BACKUP_LOG")"

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$BACKUP_LOG"
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

# Create backup
create_backup() {
    print_header "Creating Frontend Backup"
    
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_name="frontend_backup_${backup_timestamp}"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    print_message "$YELLOW" "📦 Creating backup: $backup_name"
    log "INFO" "Creating backup: $backup_name"
    
    # Check if container exists
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_message "$RED" "❌ Container not found: $CONTAINER_NAME"
        log "ERROR" "Container not found"
        exit 1
    fi
    
    # Export container
    print_message "$YELLOW" "📤 Exporting container..."
    if docker export "$CONTAINER_NAME" > "$backup_path/container.tar" 2>/dev/null; then
        print_message "$GREEN" "✅ Container exported"
        log "INFO" "Container exported successfully"
    else
        print_message "$RED" "❌ Failed to export container"
        log "ERROR" "Container export failed"
        exit 1
    fi
    
    # Save container logs
    print_message "$YELLOW" "📝 Saving container logs..."
    docker logs "$CONTAINER_NAME" > "$backup_path/container.log" 2>&1 || true
    print_message "$GREEN" "✅ Logs saved"
    
    # Save container inspect
    print_message "$YELLOW" "🔍 Saving container configuration..."
    docker inspect "$CONTAINER_NAME" > "$backup_path/container-inspect.json" 2>/dev/null || true
    print_message "$GREEN" "✅ Configuration saved"
    
    # Save image information
    print_message "$YELLOW" "🖼️  Saving image information..."
    local image_id=$(docker inspect --format='{{.Image}}' "$CONTAINER_NAME" 2>/dev/null)
    if [ -n "$image_id" ]; then
        docker inspect "$image_id" > "$backup_path/image-inspect.json" 2>/dev/null || true
        echo "$image_id" > "$backup_path/image-id.txt"
    fi
    print_message "$GREEN" "✅ Image information saved"
    
    # Save environment variables
    print_message "$YELLOW" "🔧 Saving environment variables..."
    docker exec "$CONTAINER_NAME" env > "$backup_path/environment.txt" 2>/dev/null || true
    print_message "$GREEN" "✅ Environment variables saved"
    
    # Create backup metadata
    cat > "$backup_path/metadata.json" <<EOF
{
  "backup_name": "$backup_name",
  "backup_timestamp": "$backup_timestamp",
  "container_name": "$CONTAINER_NAME",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "backup_size": "$(du -sh "$backup_path" | cut -f1)"
}
EOF
    
    # Calculate backup size
    local backup_size=$(du -sh "$backup_path" | cut -f1)
    
    print_message "$GREEN" "✅ Backup created successfully!"
    print_message "$BLUE" "   Location: $backup_path"
    print_message "$BLUE" "   Size: $backup_size"
    log "INFO" "Backup created: $backup_path (Size: $backup_size)"
    
    # Save as latest backup
    echo "$backup_path" > "$BACKUP_DIR/latest_backup.txt"
    
    # Cleanup old backups
    cleanup_old_backups
}

# Cleanup old backups
cleanup_old_backups() {
    print_header "Cleaning Up Old Backups"
    
    local backups=($(ls -dt "$BACKUP_DIR"/frontend_backup_* 2>/dev/null))
    local backup_count=${#backups[@]}
    
    if [ $backup_count -le $MAX_BACKUPS ]; then
        print_message "$GREEN" "✅ No cleanup needed ($backup_count/$MAX_BACKUPS backups)"
        log "INFO" "No cleanup needed"
        return
    fi
    
    print_message "$YELLOW" "🧹 Removing old backups (keeping $MAX_BACKUPS most recent)..."
    
    local removed_count=0
    for ((i=$MAX_BACKUPS; i<$backup_count; i++)); do
        local old_backup="${backups[$i]}"
        print_message "$YELLOW" "   Removing: $(basename "$old_backup")"
        rm -rf "$old_backup"
        removed_count=$((removed_count + 1))
    done
    
    print_message "$GREEN" "✅ Removed $removed_count old backup(s)"
    log "INFO" "Removed $removed_count old backups"
}

# List backups
list_backups() {
    print_header "Available Backups"
    
    local backups=($(ls -dt "$BACKUP_DIR"/frontend_backup_* 2>/dev/null))
    
    if [ ${#backups[@]} -eq 0 ]; then
        print_message "$YELLOW" "⚠️  No backups found"
        return
    fi
    
    echo "Total backups: ${#backups[@]}"
    echo ""
    
    for backup in "${backups[@]}"; do
        local backup_name=$(basename "$backup")
        local backup_date=$(echo "$backup_name" | sed 's/frontend_backup_//' | sed 's/_/ /')
        local backup_size=$(du -sh "$backup" | cut -f1)
        
        echo "  📦 $backup_name"
        echo "     Created: $backup_date"
        echo "     Size: $backup_size"
        echo ""
    done
}

# Main function
main() {
    print_header "Frontend Backup Utility"
    
    case "${1:-create}" in
        create)
            create_backup
            ;;
        list)
            list_backups
            ;;
        cleanup)
            cleanup_old_backups
            ;;
        *)
            echo "Usage: $0 {create|list|cleanup}"
            echo ""
            echo "Commands:"
            echo "  create  - Create a new backup (default)"
            echo "  list    - List all available backups"
            echo "  cleanup - Remove old backups (keep $MAX_BACKUPS most recent)"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

exit 0


#!/bin/bash

# iChat API Server Docker Runner
# This script provides easy commands to manage the Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="ichat-api-server"
CONTAINER_NAME="ichat-api-server"
PORT="8080"

# Functions
print_usage() {
    echo -e "${BLUE}iChat API Server Docker Manager${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build     Build the Docker image"
    echo "  run       Run the container"
    echo "  stop      Stop the container"
    echo "  restart   Restart the container"
    echo "  logs      Show container logs"
    echo "  shell     Open shell in container"
    echo "  clean     Remove container and image"
    echo "  status    Show container status"
    echo "  health    Check API health"
    echo "  compose   Use docker-compose (up/down/logs)"
    echo ""
}

build_image() {
    echo -e "${BLUE}🔨 Building iChat API Server Docker image...${NC}"
    docker build -t $IMAGE_NAME .
    echo -e "${GREEN}✅ Image built successfully!${NC}"
}

run_container() {
    echo -e "${BLUE}🚀 Starting iChat API Server container...${NC}"
    
    # Stop existing container if running
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${YELLOW}⚠️  Stopping existing container...${NC}"
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
    fi
    
    # Run new container
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:8080 \
        -e FLASK_ENV=production \
        -e FLASK_DEBUG=false \
        --restart unless-stopped \
        $IMAGE_NAME
    
    echo -e "${GREEN}✅ Container started successfully!${NC}"
    echo -e "${BLUE}📡 API available at: http://localhost:$PORT${NC}"
    echo -e "${BLUE}❤️  Health check: http://localhost:$PORT/api/health${NC}"
}

stop_container() {
    echo -e "${BLUE}🛑 Stopping iChat API Server container...${NC}"
    docker stop $CONTAINER_NAME 2>/dev/null || echo -e "${YELLOW}⚠️  Container not running${NC}"
    docker rm $CONTAINER_NAME 2>/dev/null || echo -e "${YELLOW}⚠️  Container not found${NC}"
    echo -e "${GREEN}✅ Container stopped${NC}"
}

restart_container() {
    echo -e "${BLUE}🔄 Restarting iChat API Server container...${NC}"
    stop_container
    run_container
}

show_logs() {
    echo -e "${BLUE}📋 Container logs:${NC}"
    docker logs -f $CONTAINER_NAME
}

open_shell() {
    echo -e "${BLUE}🐚 Opening shell in container...${NC}"
    docker exec -it $CONTAINER_NAME /bin/bash
}

clean_all() {
    echo -e "${BLUE}🧹 Cleaning up Docker resources...${NC}"
    stop_container
    docker rmi $IMAGE_NAME 2>/dev/null || echo -e "${YELLOW}⚠️  Image not found${NC}"
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

show_status() {
    echo -e "${BLUE}📊 Container Status:${NC}"
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${GREEN}✅ Container is running${NC}"
        docker ps -f name=$CONTAINER_NAME
    else
        echo -e "${RED}❌ Container is not running${NC}"
    fi
}

check_health() {
    echo -e "${BLUE}❤️  Checking API health...${NC}"
    if curl -s http://localhost:$PORT/api/health > /dev/null; then
        echo -e "${GREEN}✅ API is healthy!${NC}"
        curl -s http://localhost:$PORT/api/health | python3 -m json.tool
    else
        echo -e "${RED}❌ API is not responding${NC}"
    fi
}

use_compose() {
    case $2 in
        up)
            echo -e "${BLUE}🚀 Starting with docker-compose...${NC}"
            docker-compose up -d
            ;;
        down)
            echo -e "${BLUE}🛑 Stopping with docker-compose...${NC}"
            docker-compose down
            ;;
        logs)
            echo -e "${BLUE}📋 Docker-compose logs:${NC}"
            docker-compose logs -f
            ;;
        *)
            echo -e "${YELLOW}Usage: $0 compose [up|down|logs]${NC}"
            ;;
    esac
}

# Main script logic
case $1 in
    build)
        build_image
        ;;
    run)
        run_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    clean)
        clean_all
        ;;
    status)
        show_status
        ;;
    health)
        check_health
        ;;
    compose)
        use_compose $@
        ;;
    *)
        print_usage
        exit 1
        ;;
esac

#!/bin/bash

# BMEX Health Check Script
# This script checks the health of all BMEX services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is healthy
check_service() {
    local service_name=$1
    local url=$2
    local max_retries=${3:-5}
    local retry_interval=${4:-5}

    echo -n "Checking $service_name... "

    for i in $(seq 1 $max_retries); do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Healthy${NC}"
            return 0
        fi

        if [ $i -lt $max_retries ]; then
            sleep $retry_interval
        fi
    done

    echo -e "${RED}✗ Unhealthy${NC}"
    return 1
}

# Function to check Docker container status
check_container() {
    local container_name=$1
    echo -n "Checking container $container_name... "

    if docker ps --filter "name=$container_name" --filter "status=running" | grep -q "$container_name"; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

echo "=================================="
echo "BMEX Health Check"
echo "=================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

echo "Docker Containers:"
echo "------------------"
check_container "bmex-nginx" || true
check_container "bmex-backend" || true
check_container "bmex-frontend" || true
echo ""

echo "Service Endpoints:"
echo "------------------"
check_service "Nginx" "http://localhost/health" || true
check_service "Backend API" "http://localhost/api/health/" || true
check_service "Frontend" "http://localhost/masses" || true
echo ""

echo "=================================="
echo "Health check complete"
echo "=================================="

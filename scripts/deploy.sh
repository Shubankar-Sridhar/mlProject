#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Deploying Enterprise Text-to-SQL System${NC}"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}" >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose is required but not installed.${NC}" >&2; exit 1; }

# Load environment
if [ -f .env ]; then
    source .env
else
    echo -e "${YELLOW}No .env file found. Using defaults.${NC}"
fi

# Create directories
mkdir -p models/registry models/artifacts logs configs

echo -e "${GREEN}Building Docker images...${NC}"
docker-compose -f docker/docker-compose.yml build

echo -e "${GREEN}Starting services...${NC}"
docker-compose -f docker/docker-compose.yml up -d

echo -e "${GREEN}Waiting for services to be healthy...${NC}"
sleep 15

# Health check
echo -e "${GREEN}Running health check...${NC}"
if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}Health check passed!${NC}"
else
    echo -e "${RED}Health check failed!${NC}"
    docker-compose -f docker/docker-compose.yml logs
    exit 1
fi

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Frontend: http://localhost:3000"
echo -e "API: http://localhost:8000/api/v1"
echo -e "Grafana: http://localhost:3001 (admin/${GRAFANA_PASSWORD:-admin})"
echo -e "Prometheus: http://localhost:9090"
#!/bin/bash
# Deployment Script for Lenox Cat Hospital
# Deploys the application using Docker Compose

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_ROOT}/.env"
DEPLOYMENT_MODE="${1:-production}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Lenox Cat Hospital - Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Mode: ${DEPLOYMENT_MODE}"
echo "Project root: ${PROJECT_ROOT}"
echo ""

# Change to project root
cd "${PROJECT_ROOT}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

if ! command_exists docker-compose; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed${NC}"

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo "Please start Docker daemon"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon is running${NC}"

# Check for .env file
if [ ! -f "${ENV_FILE}" ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    echo "Creating .env file from template..."
    if [ -f "${PROJECT_ROOT}/.env.${DEPLOYMENT_MODE}" ]; then
        cp "${PROJECT_ROOT}/.env.${DEPLOYMENT_MODE}" "${ENV_FILE}"
        echo -e "${YELLOW}⚠ Please edit .env file and set required values${NC}"
        exit 1
    else
        echo -e "${RED}✗ No template found for ${DEPLOYMENT_MODE} mode${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ .env file exists${NC}"

# Validate critical environment variables
source "${ENV_FILE}"

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" == "change-this-to-a-random-secret-key" ]; then
    echo -e "${RED}✗ SECRET_KEY is not set or using default value${NC}"
    echo "Please set a strong SECRET_KEY in .env file"
    echo "Generate one using: openssl rand -hex 32"
    exit 1
fi
echo -e "${GREEN}✓ SECRET_KEY is configured${NC}"

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo -e "${RED}✗ POSTGRES_PASSWORD is not set${NC}"
    echo "Please set POSTGRES_PASSWORD in .env file"
    exit 1
fi
echo -e "${GREEN}✓ POSTGRES_PASSWORD is configured${NC}"

echo ""

# Determine compose files to use
COMPOSE_FILES="-f docker-compose.yml"
if [ "${DEPLOYMENT_MODE}" == "production" ]; then
    if [ -f "${PROJECT_ROOT}/docker-compose.prod.yml" ]; then
        COMPOSE_FILES="${COMPOSE_FILES} -f docker-compose.prod.yml"
        echo -e "${BLUE}Using production configuration${NC}"
    fi
elif [ "${DEPLOYMENT_MODE}" == "development" ]; then
    if [ -f "${PROJECT_ROOT}/docker-compose.dev.yml" ]; then
        COMPOSE_FILES="${COMPOSE_FILES} -f docker-compose.dev.yml"
        echo -e "${BLUE}Using development configuration${NC}"
    fi
fi

# Pull latest images
echo -e "${YELLOW}Pulling latest images...${NC}"
docker-compose ${COMPOSE_FILES} pull || true

# Build images
echo -e "${YELLOW}Building images...${NC}"
docker-compose ${COMPOSE_FILES} build --pull

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose ${COMPOSE_FILES} down || true

# Start containers
echo -e "${YELLOW}Starting containers...${NC}"
docker-compose ${COMPOSE_FILES} up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
MAX_WAIT=120  # 2 minutes
WAIT_TIME=0
INTERVAL=5

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    # Check if all services are healthy
    UNHEALTHY=$(docker-compose ${COMPOSE_FILES} ps | grep -v "Up (healthy)" | grep "Up" || true)
    if [ -z "$UNHEALTHY" ]; then
        echo -e "${GREEN}✓ All services are healthy${NC}"
        break
    fi
    echo "Waiting for services to become healthy... ($((WAIT_TIME))s / ${MAX_WAIT}s)"
    sleep $INTERVAL
    WAIT_TIME=$((WAIT_TIME + INTERVAL))
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    echo -e "${YELLOW}⚠ Services did not become healthy within ${MAX_WAIT}s${NC}"
    echo "Check container logs for issues:"
    echo "  docker-compose ${COMPOSE_FILES} logs"
fi

# Show service status
echo ""
echo -e "${BLUE}Service status:${NC}"
docker-compose ${COMPOSE_FILES} ps

# Show logs for backend (last 20 lines)
echo ""
echo -e "${BLUE}Backend logs (last 20 lines):${NC}"
docker-compose ${COMPOSE_FILES} logs --tail=20 backend

# Show application URLs
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Deployment completed successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Application URLs:${NC}"

if [ "${DEPLOYMENT_MODE}" == "production" ] && [ -n "${DOMAIN_NAME}" ]; then
    echo "  Frontend: https://${DOMAIN_NAME}"
    echo "  Backend API: https://${DOMAIN_NAME}/api"
else
    FRONTEND_PORT=$(grep "FRONTEND_PORT" "${ENV_FILE}" | cut -d'=' -f2 | tr -d ' "' || echo "80")
    BACKEND_PORT=$(grep "BACKEND_PORT" "${ENV_FILE}" | cut -d'=' -f2 | tr -d ' "' || echo "5000")
    echo "  Frontend: http://localhost:${FRONTEND_PORT}"
    echo "  Backend API: http://localhost:${BACKEND_PORT}/api"
fi

echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  View logs: docker-compose ${COMPOSE_FILES} logs -f [service]"
echo "  Stop services: docker-compose ${COMPOSE_FILES} down"
echo "  Restart service: docker-compose ${COMPOSE_FILES} restart [service]"
echo "  Run backup: docker-compose ${COMPOSE_FILES} exec backend /app/scripts/backup.sh"
echo "  Access database: docker-compose ${COMPOSE_FILES} exec postgres psql -U \$POSTGRES_USER -d \$POSTGRES_DB"

echo ""

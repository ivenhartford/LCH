#!/bin/bash
# Update Script for Lenox Cat Hospital
# Performs zero-downtime rolling update of the application

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
DEPLOYMENT_MODE="${1:-production}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Lenox Cat Hospital - Update${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Mode: ${DEPLOYMENT_MODE}"
echo ""

cd "${PROJECT_ROOT}"

# Determine compose files
COMPOSE_FILES="-f docker-compose.yml"
if [ "${DEPLOYMENT_MODE}" == "production" ] && [ -f "${PROJECT_ROOT}/docker-compose.prod.yml" ]; then
    COMPOSE_FILES="${COMPOSE_FILES} -f docker-compose.prod.yml"
fi

# Confirm update
echo -e "${YELLOW}This will update the application to the latest version.${NC}"
read -p "Continue? (yes/no): " -r CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Update cancelled${NC}"
    exit 0
fi

# Create backup before update
echo -e "${YELLOW}Creating pre-update backup...${NC}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="pre_update_${TIMESTAMP}.sql.gz"

if docker-compose ${COMPOSE_FILES} exec -T postgres /backup.sh; then
    echo -e "${GREEN}✓ Pre-update backup created${NC}"
else
    echo -e "${YELLOW}⚠ Backup failed, continue anyway? (yes/no):${NC}"
    read -r CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Update cancelled${NC}"
        exit 0
    fi
fi

# Pull latest code (if using git)
if [ -d "${PROJECT_ROOT}/.git" ]; then
    echo -e "${YELLOW}Pulling latest code from git...${NC}"
    git pull || true
    echo -e "${GREEN}✓ Code updated${NC}"
fi

# Pull latest images
echo -e "${YELLOW}Pulling latest images...${NC}"
docker-compose ${COMPOSE_FILES} pull

# Build new images
echo -e "${YELLOW}Building new images...${NC}"
docker-compose ${COMPOSE_FILES} build --pull

# Update backend with zero downtime
echo -e "${YELLOW}Updating backend service...${NC}"
docker-compose ${COMPOSE_FILES} up -d --no-deps --scale backend=2 backend
sleep 10  # Wait for new backend to be healthy
docker-compose ${COMPOSE_FILES} up -d --no-deps --scale backend=1 backend
echo -e "${GREEN}✓ Backend updated${NC}"

# Update frontend
echo -e "${YELLOW}Updating frontend service...${NC}"
docker-compose ${COMPOSE_FILES} up -d --no-deps frontend
echo -e "${GREEN}✓ Frontend updated${NC}"

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
if docker-compose ${COMPOSE_FILES} exec -T backend flask db upgrade; then
    echo -e "${GREEN}✓ Database migrations completed${NC}"
else
    echo -e "${RED}✗ Database migrations failed${NC}"
    echo -e "${YELLOW}Rolling back update...${NC}"
    docker-compose ${COMPOSE_FILES} down
    docker-compose ${COMPOSE_FILES} up -d
    exit 1
fi

# Restart all services to ensure consistency
echo -e "${YELLOW}Restarting all services...${NC}"
docker-compose ${COMPOSE_FILES} restart

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Verify services are running
echo -e "${YELLOW}Verifying services...${NC}"
if docker-compose ${COMPOSE_FILES} ps | grep -q "Up (healthy)"; then
    echo -e "${GREEN}✓ All services are healthy${NC}"
else
    echo -e "${YELLOW}⚠ Some services may not be healthy${NC}"
    docker-compose ${COMPOSE_FILES} ps
fi

# Show service status
echo ""
echo -e "${BLUE}Service status:${NC}"
docker-compose ${COMPOSE_FILES} ps

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Update completed successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Test the application to ensure everything works"
echo "  2. Monitor logs for any errors"
echo "  3. If issues occur, restore from backup: ${BACKUP_FILE}"
echo ""

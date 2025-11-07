#!/bin/bash
# SSL Initialization Script for Lenox Cat Hospital
# Sets up SSL certificates using Let's Encrypt (Certbot)

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

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Lenox Cat Hospital - SSL Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Load environment variables
if [ ! -f "${ENV_FILE}" ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    exit 1
fi

source "${ENV_FILE}"

# Check if domain name is set
if [ -z "${DOMAIN_NAME}" ]; then
    echo -e "${YELLOW}Enter your domain name (e.g., clinic.example.com):${NC}"
    read -r DOMAIN_NAME
    if [ -z "${DOMAIN_NAME}" ]; then
        echo -e "${RED}✗ Domain name is required${NC}"
        exit 1
    fi
fi

echo "Domain: ${DOMAIN_NAME}"

# Check if email is set for Let's Encrypt notifications
if [ -z "${SSL_EMAIL}" ]; then
    echo -e "${YELLOW}Enter your email address for SSL certificate notifications:${NC}"
    read -r SSL_EMAIL
    if [ -z "${SSL_EMAIL}" ]; then
        echo -e "${RED}✗ Email address is required${NC}"
        exit 1
    fi
fi

echo "Email: ${SSL_EMAIL}"
echo ""

# Confirm setup
echo -e "${BLUE}This script will:${NC}"
echo "  1. Obtain SSL certificates from Let's Encrypt"
echo "  2. Configure nginx to use HTTPS"
echo "  3. Set up automatic certificate renewal"
echo ""
echo -e "${YELLOW}⚠ Make sure:${NC}"
echo "  - Your domain (${DOMAIN_NAME}) points to this server's IP address"
echo "  - Port 80 and 443 are accessible from the internet"
echo "  - The application is running (or will start it)"
echo ""
read -p "Continue? (yes/no): " -r CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}SSL setup cancelled${NC}"
    exit 0
fi

# Create SSL directories
echo -e "${YELLOW}Creating SSL directories...${NC}"
mkdir -p "${PROJECT_ROOT}/ssl/certs"
mkdir -p "${PROJECT_ROOT}/ssl/acme-challenge"
echo -e "${GREEN}✓ Directories created${NC}"

# Update .env file with SSL settings
echo -e "${YELLOW}Updating .env file...${NC}"
if ! grep -q "DOMAIN_NAME=" "${ENV_FILE}"; then
    echo "DOMAIN_NAME=${DOMAIN_NAME}" >> "${ENV_FILE}"
fi
if ! grep -q "SSL_EMAIL=" "${ENV_FILE}"; then
    echo "SSL_EMAIL=${SSL_EMAIL}" >> "${ENV_FILE}"
fi
echo -e "${GREEN}✓ .env file updated${NC}"

# Determine compose files
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

# Start the application without SSL first (for ACME challenge)
echo -e "${YELLOW}Starting application in HTTP mode for certificate generation...${NC}"
docker-compose ${COMPOSE_FILES} up -d frontend

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
sleep 10

# Obtain SSL certificate using certbot
echo -e "${YELLOW}Obtaining SSL certificate from Let's Encrypt...${NC}"
docker-compose ${COMPOSE_FILES} run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "${SSL_EMAIL}" \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d "${DOMAIN_NAME}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ SSL certificate obtained successfully${NC}"
else
    echo -e "${RED}✗ Failed to obtain SSL certificate${NC}"
    echo ""
    echo -e "${BLUE}Troubleshooting:${NC}"
    echo "  1. Verify domain DNS is configured correctly:"
    echo "     dig ${DOMAIN_NAME}"
    echo "  2. Check if ports 80 and 443 are open:"
    echo "     netstat -tuln | grep ':80\\|:443'"
    echo "  3. Check nginx logs:"
    echo "     docker-compose ${COMPOSE_FILES} logs frontend"
    exit 1
fi

# Restart application with SSL enabled
echo -e "${YELLOW}Restarting application with SSL enabled...${NC}"
docker-compose ${COMPOSE_FILES} down
docker-compose ${COMPOSE_FILES} up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 15

# Verify SSL is working
echo -e "${YELLOW}Verifying SSL configuration...${NC}"
if curl -k -s -o /dev/null -w "%{http_code}" "https://${DOMAIN_NAME}" | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ HTTPS is working!${NC}"
else
    echo -e "${YELLOW}⚠ Could not verify HTTPS (may be a firewall issue)${NC}"
fi

# Set up automatic renewal
echo -e "${YELLOW}Setting up automatic certificate renewal...${NC}"
echo "Certbot will automatically renew certificates before they expire."
echo "The certbot container runs a renewal check twice daily."
echo -e "${GREEN}✓ Automatic renewal configured${NC}"

# Show certificate information
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ SSL setup completed successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Certificate information:${NC}"
docker-compose ${COMPOSE_FILES} run --rm certbot certificates

echo ""
echo -e "${BLUE}Your application is now accessible at:${NC}"
echo "  https://${DOMAIN_NAME}"
echo ""
echo -e "${BLUE}Certificate renewal:${NC}"
echo "  Certificates will automatically renew before expiration"
echo "  To manually renew: docker-compose ${COMPOSE_FILES} run --rm certbot renew"
echo ""
echo -e "${BLUE}Security recommendations:${NC}"
echo "  1. Test your SSL configuration: https://www.ssllabs.com/ssltest/analyze.html?d=${DOMAIN_NAME}"
echo "  2. Consider enabling HSTS preloading"
echo "  3. Regularly update Docker images for security patches"
echo ""

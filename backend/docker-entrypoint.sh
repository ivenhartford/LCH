#!/bin/bash
# Backend Entrypoint Script for Lenox Cat Hospital
# This script initializes the backend service with configurable parameters

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Lenox Cat Hospital - Backend Starting${NC}"
echo -e "${GREEN}========================================${NC}"

# Display configuration (without sensitive data)
echo -e "${YELLOW}Configuration:${NC}"
echo "  Flask Environment: ${FLASK_ENV:-production}"
echo "  Backend Host: ${FLASK_RUN_HOST:-0.0.0.0}"
echo "  Backend Port: ${FLASK_RUN_PORT:-5000}"
echo "  Gunicorn Workers: ${GUNICORN_WORKERS:-4}"
echo "  Gunicorn Timeout: ${GUNICORN_TIMEOUT:-120}s"
echo "  Database Wait Time: ${DB_WAIT_TIME:-5}s"
echo "  Log Level: ${LOG_LEVEL:-INFO}"

# Wait for database to be ready
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
sleep "${DB_WAIT_TIME:-5}"

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
if flask db upgrade; then
    echo -e "${GREEN}✓ Database migrations completed${NC}"
else
    echo -e "${RED}✗ Database migrations failed${NC}"
    exit 1
fi

# Optional: Create initial admin user if configured
if [ -n "${INITIAL_ADMIN_USERNAME}" ] && [ -n "${INITIAL_ADMIN_PASSWORD}" ]; then
    echo -e "${YELLOW}Checking for initial admin user...${NC}"
    python << END
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    # Check if admin user already exists
    admin_user = User.query.filter_by(username='${INITIAL_ADMIN_USERNAME}').first()
    if not admin_user:
        print('Creating initial admin user...')
        admin = User(
            username='${INITIAL_ADMIN_USERNAME}',
            role='${INITIAL_ADMIN_ROLE:-administrator}'
        )
        admin.set_password('${INITIAL_ADMIN_PASSWORD}')
        db.session.add(admin)
        db.session.commit()
        print('✓ Initial admin user created: ${INITIAL_ADMIN_USERNAME}')
        print('⚠ IMPORTANT: Change the admin password immediately after first login!')
    else:
        print('Admin user already exists, skipping creation.')
END
fi

# Start the backend server with Gunicorn
echo -e "${GREEN}Starting backend server...${NC}"
echo "  Binding to: ${FLASK_RUN_HOST:-0.0.0.0}:${FLASK_RUN_PORT:-5000}"
echo "  Workers: ${GUNICORN_WORKERS:-4}"
echo "  Worker Class: ${GUNICORN_WORKER_CLASS:-sync}"
echo "  Timeout: ${GUNICORN_TIMEOUT:-120}s"
echo "  Max Requests: ${GUNICORN_MAX_REQUESTS:-1000}"
echo -e "${GREEN}========================================${NC}"

exec gunicorn \
    --bind "${FLASK_RUN_HOST:-0.0.0.0}:${FLASK_RUN_PORT:-5000}" \
    --workers "${GUNICORN_WORKERS:-4}" \
    --worker-class "${GUNICORN_WORKER_CLASS:-sync}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --max-requests "${GUNICORN_MAX_REQUESTS:-1000}" \
    --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER:-50}" \
    --access-logfile "${GUNICORN_ACCESS_LOG:--}" \
    --error-logfile "${GUNICORN_ERROR_LOG:--}" \
    --log-level "${LOG_LEVEL:-info}" \
    "app:create_app()"

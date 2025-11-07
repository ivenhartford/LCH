#!/bin/sh
# Frontend Entrypoint Script for Lenox Cat Hospital
# This script substitutes environment variables in nginx configuration

set -e  # Exit on error

echo "========================================"
echo "Lenox Cat Hospital - Frontend Starting"
echo "========================================"

# Display configuration
echo "Configuration:"
echo "  Backend Host: ${BACKEND_HOST:-backend}"
echo "  Backend Port: ${BACKEND_PORT:-5000}"
echo "  Frontend Port: ${FRONTEND_INTERNAL_PORT:-80}"
echo "  Nginx Workers: ${NGINX_WORKER_PROCESSES:-auto}"
echo "  Nginx Connections: ${NGINX_WORKER_CONNECTIONS:-1024}"
echo "  Gzip Min Length: ${NGINX_GZIP_MIN_LENGTH:-1024}"
echo "  Proxy Timeout: ${NGINX_PROXY_TIMEOUT:-120}s"

# Substitute environment variables in nginx configuration
echo "Substituting environment variables in nginx configuration..."
envsubst '
    ${BACKEND_HOST}
    ${BACKEND_PORT}
    ${FRONTEND_INTERNAL_PORT}
    ${NGINX_WORKER_PROCESSES}
    ${NGINX_WORKER_CONNECTIONS}
    ${NGINX_GZIP_MIN_LENGTH}
    ${NGINX_PROXY_TIMEOUT}
    ${NGINX_STATIC_CACHE_TIME}
' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "✓ Nginx configuration ready"
echo "========================================"

# Execute the CMD passed to docker (nginx in this case)
exec "$@"

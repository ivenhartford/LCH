#!/bin/sh
# Frontend Production Entrypoint Script for Lenox Cat Hospital
# This script configures nginx for either HTTP or HTTPS based on SSL certificate availability

set -e  # Exit on error

echo "========================================"
echo "Lenox Cat Hospital - Frontend (Production)"
echo "========================================"

# Display configuration
echo "Configuration:"
echo "  Backend Host: ${BACKEND_HOST:-backend}"
echo "  Backend Port: ${BACKEND_PORT:-5000}"
echo "  Nginx Workers: ${NGINX_WORKER_PROCESSES:-auto}"
echo "  Nginx Connections: ${NGINX_WORKER_CONNECTIONS:-1024}"
echo "  Gzip Min Length: ${NGINX_GZIP_MIN_LENGTH:-1024}"
echo "  Proxy Timeout: ${NGINX_PROXY_TIMEOUT:-120}s"

# Determine which nginx configuration to use
if [ -n "${DOMAIN_NAME}" ] && [ -f "${SSL_CERTIFICATE_PATH:-/etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem}" ]; then
    echo "SSL Mode: ENABLED"
    echo "  Domain: ${DOMAIN_NAME}"
    echo "  Certificate: ${SSL_CERTIFICATE_PATH:-/etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem}"
    CONFIG_TEMPLATE="/etc/nginx/templates/nginx-ssl.conf.template"

    # Substitute environment variables for SSL configuration
    echo "Substituting environment variables for SSL nginx configuration..."
    envsubst '
        ${BACKEND_HOST}
        ${BACKEND_PORT}
        ${NGINX_WORKER_PROCESSES}
        ${NGINX_WORKER_CONNECTIONS}
        ${NGINX_GZIP_MIN_LENGTH}
        ${NGINX_PROXY_TIMEOUT}
        ${NGINX_STATIC_CACHE_TIME}
        ${DOMAIN_NAME}
        ${SSL_CERTIFICATE_PATH}
        ${SSL_CERTIFICATE_KEY_PATH}
        ${SSL_CHAIN_PATH}
    ' < "$CONFIG_TEMPLATE" > /etc/nginx/conf.d/default.conf
else
    echo "SSL Mode: DISABLED (using HTTP only)"
    echo "  To enable SSL, ensure DOMAIN_NAME is set and SSL certificates are mounted"
    CONFIG_TEMPLATE="/etc/nginx/templates/nginx-http.conf.template"

    # Substitute environment variables for HTTP-only configuration
    echo "Substituting environment variables for HTTP nginx configuration..."
    envsubst '
        ${BACKEND_HOST}
        ${BACKEND_PORT}
        ${FRONTEND_INTERNAL_PORT}
        ${NGINX_WORKER_PROCESSES}
        ${NGINX_WORKER_CONNECTIONS}
        ${NGINX_GZIP_MIN_LENGTH}
        ${NGINX_PROXY_TIMEOUT}
        ${NGINX_STATIC_CACHE_TIME}
    ' < "$CONFIG_TEMPLATE" > /etc/nginx/conf.d/default.conf
fi

echo "✓ Nginx configuration ready"

# Test nginx configuration
echo "Testing nginx configuration..."
if nginx -t; then
    echo "✓ Nginx configuration is valid"
else
    echo "✗ Nginx configuration test failed"
    exit 1
fi

echo "========================================"
echo "Starting nginx..."

# Execute the CMD passed to docker (nginx in this case)
exec "$@"

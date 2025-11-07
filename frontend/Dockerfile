# Frontend Dockerfile for Lenox Cat Hospital
# Multi-stage build for optimized production image
# All configurable values managed via build arguments and environment variables

# Build arguments
ARG NODE_VERSION=18-alpine

# Stage 1: Build the React application
FROM node:${NODE_VERSION} AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy application source
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Install envsubst for environment variable substitution
RUN apk add --no-cache gettext

# Copy nginx configuration template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy built application from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Expose port (configurable via environment variable)
EXPOSE ${FRONTEND_INTERNAL_PORT:-80}

# Health check (intervals set in docker-compose.yml)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:${FRONTEND_INTERNAL_PORT:-80}/ || exit 1

# Use custom entrypoint to substitute environment variables in nginx config
ENTRYPOINT ["/docker-entrypoint.sh"]

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

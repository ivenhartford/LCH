# Backend Dockerfile for Lenox Cat Hospital
# All configurable values are now managed via build arguments and environment variables

# Build arguments for customization
ARG PYTHON_VERSION=3.11-slim

FROM python:${PYTHON_VERSION}

# Build-time arguments
ARG APP_DIR_PERMISSIONS=755

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app:create_app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create necessary directories with configurable permissions
RUN mkdir -p /app/logs /app/instance /app/uploads && \
    chmod -R ${APP_DIR_PERMISSIONS} /app/logs /app/instance /app/uploads

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose port (will be configured via environment variable at runtime)
EXPOSE ${BACKEND_INTERNAL_PORT:-5000}

# Health check with configurable intervals (set in docker-compose.yml)
# Note: HEALTHCHECK in Dockerfile is overridden by docker-compose.yml
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${BACKEND_INTERNAL_PORT:-5000}/api/health').read()" || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

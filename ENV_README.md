# Environment Configuration Guide

This document explains all environment variables used in the Lenox Cat Hospital Docker deployment.

## Quick Start

1. **For Development:**
   ```bash
   cp .env.development .env
   # Edit .env if needed, then:
   docker compose up
   ```

2. **For Production:**
   ```bash
   cp .env.production .env
   # IMPORTANT: Edit .env and change ALL security-sensitive values!
   # Then:
   docker compose up -d
   ```

3. **Custom Configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your custom values
   docker compose up
   ```

## Environment Files

| File | Purpose | Security |
|------|---------|----------|
| `.env` | Main configuration file (DO NOT commit to git) | Contains secrets |
| `.env.example` | Minimal template | Safe to commit |
| `.env.development` | Development defaults | Weak credentials OK |
| `.env.production` | Production template | CHANGE ALL VALUES |

## Critical Security Variables

⚠️ **MUST CHANGE** these values before production deployment:

### SECRET_KEY
**Required for production**

Flask application secret key used for session encryption and security.

```bash
# Generate a secure key:
python -c 'import secrets; print(secrets.token_hex(32))'

# Set in .env:
SECRET_KEY=your_generated_64_character_hex_string
```

### POSTGRES_PASSWORD
**Required for all environments**

PostgreSQL database password.

```bash
# Production: Use a strong password
POSTGRES_PASSWORD=your_strong_database_password_here

# Development: Can be simple
POSTGRES_PASSWORD=dev_password_123
```

### INITIAL_ADMIN_PASSWORD
**Change immediately after first login**

Password for the initial administrator account.

```bash
INITIAL_ADMIN_PASSWORD=temporary_change_on_first_login
```

## Application Configuration

### FLASK_ENV
**Default: `production`**

Application environment mode.

- `development` - Debug mode, verbose logging, auto-reload
- `production` - Optimized, minimal logging, no debug
- `testing` - For automated tests

```bash
FLASK_ENV=production
```

### APP_NAME
**Default: `Lenox Cat Hospital`**

Application name (used in logs and display).

```bash
APP_NAME=Lenox Cat Hospital
```

## Database Configuration

### POSTGRES_VERSION
**Default: `15-alpine`**

PostgreSQL Docker image version.

```bash
POSTGRES_VERSION=15-alpine
```

### POSTGRES_DB
**Default: `vet_clinic_db`**

Database name.

```bash
POSTGRES_DB=vet_clinic_db
```

### POSTGRES_USER
**Default: `vet_clinic_user`**

Database user name.

```bash
POSTGRES_USER=vet_clinic_user
```

### POSTGRES_PORT
**Default: `5432`**

External port for PostgreSQL (host machine).

```bash
POSTGRES_PORT=5432  # Can change if port conflicts
```

### Database Health Check Settings

```bash
DB_HEALTH_CHECK_INTERVAL=10s     # How often to check
DB_HEALTH_CHECK_TIMEOUT=5s       # Max time per check
DB_HEALTH_CHECK_RETRIES=5        # Retries before marking unhealthy
DB_HEALTH_CHECK_START_PERIOD=10s # Grace period on startup
```

## Backend (API) Configuration

### Ports

```bash
BACKEND_PORT=5000          # External port (host machine)
BACKEND_INTERNAL_PORT=5000 # Internal container port
BACKEND_HOST=0.0.0.0       # Listen address (0.0.0.0 = all interfaces)
```

### Gunicorn (Production Server) Settings

```bash
GUNICORN_WORKERS=4                  # Number of worker processes
                                    # Formula: (2 x CPU_CORES) + 1

GUNICORN_TIMEOUT=120                # Worker timeout in seconds

GUNICORN_WORKER_CLASS=sync          # Worker type: sync, gevent, eventlet

GUNICORN_MAX_REQUESTS=1000          # Restart worker after N requests
                                    # (prevents memory leaks)

GUNICORN_MAX_REQUESTS_JITTER=50     # Randomize restart to avoid stampede

GUNICORN_ACCESS_LOG=-               # - = stdout, or path to file
GUNICORN_ERROR_LOG=-                # - = stderr, or path to file
```

### Backend Health Check Settings

```bash
BACKEND_HEALTH_CHECK_INTERVAL=30s
BACKEND_HEALTH_CHECK_TIMEOUT=10s
BACKEND_HEALTH_CHECK_RETRIES=3
BACKEND_HEALTH_CHECK_START_PERIOD=40s  # Backend needs time to start
```

### Startup Configuration

```bash
DB_WAIT_TIME=5  # Seconds to wait for database before migrations
```

## Frontend (Web UI) Configuration

### Ports

```bash
FRONTEND_PORT=80           # External port (host machine)
FRONTEND_INTERNAL_PORT=80  # Internal container port
```

### Nginx Settings

```bash
NGINX_WORKER_PROCESSES=auto        # auto = number of CPU cores
NGINX_WORKER_CONNECTIONS=1024      # Max connections per worker
NGINX_GZIP_MIN_LENGTH=1024         # Min size to compress (bytes)
NGINX_PROXY_TIMEOUT=120            # Timeout for backend requests (seconds)
NGINX_STATIC_CACHE_TIME=1y         # Cache duration for static files
```

### Frontend Health Check Settings

```bash
FRONTEND_HEALTH_CHECK_INTERVAL=30s
FRONTEND_HEALTH_CHECK_TIMEOUT=10s
FRONTEND_HEALTH_CHECK_RETRIES=3
FRONTEND_HEALTH_CHECK_START_PERIOD=10s
```

## Build Configuration

### PYTHON_VERSION
**Default: `3.11-slim`**

Python Docker image version for backend.

```bash
PYTHON_VERSION=3.11-slim
```

### NODE_VERSION
**Default: `18-alpine`**

Node.js Docker image version for frontend build.

```bash
NODE_VERSION=18-alpine
```

### APP_DIR_PERMISSIONS
**Default: `755`**

File permissions for application directories.

```bash
APP_DIR_PERMISSIONS=755  # rwxr-xr-x
```

## Network & Container Configuration

### Container Names

```bash
CONTAINER_PREFIX=lch
POSTGRES_CONTAINER_NAME=lch-postgres
BACKEND_CONTAINER_NAME=lch-backend
FRONTEND_CONTAINER_NAME=lch-frontend
```

### Network Configuration

```bash
NETWORK_NAME=lch-network
NETWORK_DRIVER=bridge
NETWORK_SUBNET=172.28.0.0/16
```

### Volume Names

```bash
POSTGRES_VOLUME_NAME=lch-postgres-data
BACKEND_LOGS_VOLUME_NAME=lch-backend-logs
BACKEND_UPLOADS_VOLUME_NAME=lch-backend-uploads
BACKEND_INSTANCE_VOLUME_NAME=lch-backend-instance
```

### Restart Policy

```bash
RESTART_POLICY=unless-stopped
# Options: no, always, on-failure, unless-stopped
```

## Security Configuration

### CORS Configuration

```bash
# Comma-separated list of allowed origins
CORS_ORIGINS=http://localhost,http://localhost:80,https://yourdomain.com
```

### Session Configuration

```bash
SESSION_COOKIE_SECURE=true        # Require HTTPS (set false for dev)
SESSION_COOKIE_HTTPONLY=true      # Prevent JavaScript access
SESSION_COOKIE_SAMESITE=Lax       # CSRF protection: Lax, Strict, None
PERMANENT_SESSION_LIFETIME=3600   # Session duration in seconds (1 hour)
```

### Production Security Flags

```bash
ENABLE_HTTPS_REDIRECT=false  # Redirect HTTP to HTTPS
ENABLE_HSTS=false            # HTTP Strict Transport Security
ENABLE_CSP=false             # Content Security Policy
```

## Initial Admin User

These variables create an admin user on first startup. The user is NOT created if it already exists.

```bash
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=CHANGE_IMMEDIATELY
INITIAL_ADMIN_ROLE=administrator
```

⚠️ **Important:** Change the password immediately after first login!

## Logging Configuration

```bash
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR, CRITICAL
REACT_APP_LOG_LEVEL=INFO           # Frontend log level
REACT_APP_LOG_TO_BACKEND=false     # Send frontend logs to backend
```

## Time Zone Configuration

```bash
TZ=America/New_York                # Container timezone
POSTGRES_TIMEZONE=America/New_York # Database timezone
```

[See all timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

## File Upload Configuration

```bash
MAX_UPLOAD_SIZE=16M  # Maximum file upload size

ALLOWED_EXTENSIONS=pdf,doc,docx,txt,rtf,jpg,jpeg,png,gif,bmp,tiff,xls,xlsx,csv,zip,rar
```

## Development-Only Settings

⚠️ **Never enable in production:**

```bash
FLASK_DEBUG=true        # Enable Flask debugger
SQLALCHEMY_ECHO=true    # Log all SQL queries
```

## Backup Configuration

```bash
BACKUP_RETENTION_DAYS=30   # How long to keep backups
BACKUP_SCHEDULE=0 2 * * *  # Cron schedule (2 AM daily)
```

## Rate Limiting

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE_URL=memory://
```

## Complete Example Files

### Minimal Production .env

```bash
# Minimal production configuration
FLASK_ENV=production
SECRET_KEY=<generate_with_secrets_module>
POSTGRES_PASSWORD=<strong_password>
INITIAL_ADMIN_PASSWORD=<change_after_first_login>

# Use defaults for everything else
```

### Development .env

```bash
# Development configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=dev-key-not-for-production
POSTGRES_PASSWORD=dev123
INITIAL_ADMIN_PASSWORD=admin123
GUNICORN_WORKERS=2
LOG_LEVEL=DEBUG
```

### Full Production .env

See `.env.production` for a complete production template.

## Environment Variable Priority

Docker Compose resolves environment variables in this order:

1. **Compose file** (docker-compose.yml)
2. **Environment file** (.env)
3. **Shell environment** (exported variables)
4. **Default values** (in docker-compose.yml with `:-` syntax)

## Troubleshooting

### Variables Not Being Used

```bash
# Make sure your .env file is in the same directory as docker-compose.yml
ls -la .env

# Load .env explicitly:
docker compose --env-file .env up

# Check what values Docker Compose is using:
docker compose config
```

### Secrets in Logs

Never log sensitive variables:
```bash
# Bad - logs password
echo "Password: $POSTGRES_PASSWORD"

# Good - confirms it's set without revealing value
echo "Password: ${POSTGRES_PASSWORD:+SET}"
```

### Permission Denied

If entrypoint scripts fail:
```bash
chmod +x backend/docker-entrypoint.sh
chmod +x frontend/docker-entrypoint.sh
```

## Security Best Practices

1. ✅ **Never commit `.env` to git** (it's in .gitignore)
2. ✅ **Use `.env.example` for templates** (safe to commit)
3. ✅ **Generate strong SECRET_KEY** (use secrets module)
4. ✅ **Use strong database passwords** (mix of chars, numbers, symbols)
5. ✅ **Change INITIAL_ADMIN_PASSWORD** immediately after first login
6. ✅ **Enable SESSION_COOKIE_SECURE** in production (requires HTTPS)
7. ✅ **Set specific CORS_ORIGINS** (don't use wildcards)
8. ✅ **Keep sensitive vars in .env** (not in docker-compose.yml)

## Additional Resources

- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Flask Configuration](https://flask.palletsprojects.com/en/2.3.x/config/)
- [Gunicorn Settings](https://docs.gunicorn.org/en/stable/settings.html)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [PostgreSQL Environment Variables](https://www.postgresql.org/docs/current/libpq-envars.html)

---

**For deployment help, see [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)**

# Docker Guide - Lenox Cat Hospital

This guide provides comprehensive instructions for running the Lenox Cat Hospital application using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
- [Common Operations](#common-operations)
- [Development with Docker](#development-with-docker)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Docker Engine** 20.10 or higher ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0 or higher ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git** (to clone the repository)

Verify your installation:

```bash
docker --version
docker compose version
```

## Quick Start

Get the application up and running in 5 minutes:

### 1. Clone the Repository (if not already done)

```bash
git clone <repository-url>
cd LCH
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.docker.example .env.docker

# Edit the file and change the SECRET_KEY and passwords
nano .env.docker  # or use your preferred editor
```

**Important:** Change these values in `.env.docker`:
- `SECRET_KEY` - Generate with: `python -c 'import secrets; print(secrets.token_hex(32))'`
- `POSTGRES_PASSWORD` - Use a strong password

### 3. Start All Services

```bash
# Start all services in detached mode
docker compose --env-file .env.docker up -d

# View logs to ensure everything started correctly
docker compose logs -f
```

### 4. Access the Application

Once all services are healthy (check with `docker compose ps`):

- **Frontend (Web App):** http://localhost
- **Backend API:** http://localhost:5000
- **API Documentation:** http://localhost:5000/api/doc

### 5. Create Admin User

```bash
# Access the backend container
docker compose exec backend flask shell

# In the Flask shell, create an admin user:
```

```python
from app import db
from app.models import User

admin = User(username='admin', role='administrator')
admin.set_password('admin123')  # Change this password!
db.session.add(admin)
db.session.commit()
print("Admin user created successfully!")
exit()
```

### 6. (Optional) Seed Default Data

```bash
# Seed appointment types
docker compose exec backend python seed_data.py
```

### 7. Login

Navigate to http://localhost and login with:
- **Username:** `admin`
- **Password:** `admin123` (or what you set)

## Architecture Overview

The Docker setup consists of three main services:

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│              (React + Nginx)                     │
│                 Port: 80                         │
└────────────────┬────────────────────────────────┘
                 │
                 │ Proxies /api requests
                 ▼
┌─────────────────────────────────────────────────┐
│                   Backend                        │
│              (Flask + Gunicorn)                  │
│                 Port: 5000                       │
└────────────────┬────────────────────────────────┘
                 │
                 │ Database connection
                 ▼
┌─────────────────────────────────────────────────┐
│                  PostgreSQL                      │
│                 Port: 5432                       │
└─────────────────────────────────────────────────┘
```

### Services

1. **postgres** - PostgreSQL 15 database
   - Stores all application data
   - Persistent volume for data
   - Health checks enabled

2. **backend** - Flask API server
   - Runs with Gunicorn (4 workers)
   - Automatic database migrations on startup
   - Health check endpoint
   - Persistent volumes for logs and uploads

3. **frontend** - React application
   - Multi-stage build (build + nginx)
   - Optimized production bundle
   - Nginx reverse proxy for API

### Networks

All services communicate on the `lch-network` bridge network.

### Volumes

Persistent data storage:
- `lch-postgres-data` - Database data
- `lch-backend-logs` - Application logs
- `lch-backend-uploads` - Uploaded files
- `lch-backend-instance` - Flask instance data

## Configuration

### Environment Variables

Create `.env.docker` from the example:

```bash
cp .env.docker.example .env.docker
```

Key variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_ENV` | Application environment | `production` | No |
| `SECRET_KEY` | Flask secret key | - | **Yes** |
| `POSTGRES_DB` | Database name | `vet_clinic_db` | No |
| `POSTGRES_USER` | Database user | `vet_clinic_user` | No |
| `POSTGRES_PASSWORD` | Database password | - | **Yes** |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | No |
| `BACKEND_PORT` | Backend API port | `5000` | No |
| `FRONTEND_PORT` | Frontend web port | `80` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost` | No |

### Port Customization

To run on different ports, edit `.env.docker`:

```bash
FRONTEND_PORT=8080    # Access frontend at http://localhost:8080
BACKEND_PORT=5001     # Backend API at http://localhost:5001
POSTGRES_PORT=5433    # PostgreSQL at localhost:5433
```

## Common Operations

### Starting Services

```bash
# Start all services
docker compose --env-file .env.docker up -d

# Start specific service
docker compose up -d backend

# Start with live logs
docker compose --env-file .env.docker up
```

### Stopping Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# Last 100 lines
docker compose logs --tail=100 backend
```

### Checking Service Status

```bash
# List running services and their status
docker compose ps

# Check health status
docker compose ps --format json | jq '.[] | {name: .Name, status: .Status, health: .Health}'
```

### Accessing Containers

```bash
# Backend shell
docker compose exec backend bash

# Frontend shell
docker compose exec frontend sh

# PostgreSQL shell
docker compose exec postgres psql -U vet_clinic_user -d vet_clinic_db

# Flask shell
docker compose exec backend flask shell
```

### Database Operations

```bash
# Run migrations
docker compose exec backend flask db upgrade

# Create a new migration
docker compose exec backend flask db migrate -m "Description"

# Rollback last migration
docker compose exec backend flask db downgrade

# Database backup
docker compose exec postgres pg_dump -U vet_clinic_user vet_clinic_db > backup_$(date +%Y%m%d).sql

# Database restore
docker compose exec -T postgres psql -U vet_clinic_user -d vet_clinic_db < backup_20250101.sql
```

### Rebuilding Services

```bash
# Rebuild all images
docker compose build

# Rebuild specific service
docker compose build backend

# Rebuild without cache
docker compose build --no-cache

# Rebuild and restart
docker compose up -d --build
```

## Development with Docker

### Development Mode

For development with live code reloading, use volume mounts:

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    volumes:
      - ./backend:/app
      - backend_venv:/app/venv
    environment:
      FLASK_ENV: development
      FLASK_DEBUG: 1
    command: flask run --host=0.0.0.0 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    environment:
      - CHOKIDAR_USEPOLLING=true
    command: npm start

volumes:
  backend_venv:
```

Run in development mode:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.docker up
```

### Running Tests

```bash
# Backend tests
docker compose exec backend pytest backend/tests -v

# Backend tests with coverage
docker compose exec backend pytest backend/tests --cov=backend/app

# Frontend tests
docker compose exec frontend npm test
```

### Debugging

Access Python debugger:

```bash
# Add this to your code where you want to break
import pdb; pdb.set_trace()

# Then run the service without detached mode
docker compose up backend
```

## Production Deployment

### Security Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Change `POSTGRES_PASSWORD` to a strong password
- [ ] Set `FLASK_ENV=production`
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS (use a reverse proxy like nginx or Caddy)
- [ ] Set up proper firewall rules
- [ ] Regular database backups
- [ ] Monitor logs and set up alerts

### Using HTTPS

For production, use a reverse proxy with SSL:

**Example nginx reverse proxy:**

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Or use [Caddy](https://caddyserver.com/) for automatic HTTPS:

```
your-domain.com {
    reverse_proxy localhost:80
}
```

### Scaling

Scale the backend service:

```bash
# Run multiple backend workers
docker compose up -d --scale backend=3
```

For production load balancing, consider using:
- Docker Swarm
- Kubernetes
- AWS ECS/EKS
- Cloud services (Railway, Render, Fly.io)

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker compose logs
```

**Common issues:**
- Port already in use: Change ports in `.env.docker`
- Permission denied: Run with sudo or add user to docker group
- Database not ready: Backend will retry automatically

### Database Connection Errors

```bash
# Check if postgres is healthy
docker compose ps postgres

# View postgres logs
docker compose logs postgres

# Verify connection string
docker compose exec backend env | grep DATABASE_URL
```

### Frontend Can't Reach Backend

**Check nginx configuration:**
```bash
docker compose exec frontend cat /etc/nginx/conf.d/default.conf
```

**Test backend directly:**
```bash
curl http://localhost:5000/api/health
```

### Out of Disk Space

**Clean up Docker:**
```bash
# Remove unused containers, networks, images
docker system prune -a

# Remove unused volumes (WARNING: deletes data)
docker volume prune
```

**Check volume sizes:**
```bash
docker system df -v
```

### Performance Issues

**Check resource usage:**
```bash
docker stats
```

**Increase resources:**
- Docker Desktop: Settings → Resources → Adjust CPU/Memory
- Linux: No limits by default

### Reset Everything

```bash
# Stop all services
docker compose down

# Remove all volumes (WARNING: deletes all data)
docker compose down -v

# Remove images
docker compose down --rmi all

# Start fresh
docker compose --env-file .env.docker up -d
```

## Maintenance

### Regular Tasks

**Daily:**
- Monitor logs for errors
- Check service health status

**Weekly:**
- Review disk usage
- Check for Docker image updates
- Review application logs

**Monthly:**
- Database backup
- Update dependencies
- Security updates

### Backups

**Automated backup script** (`backup.sh`):

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

mkdir -p $BACKUP_DIR

# Database backup
docker compose exec -T postgres pg_dump -U vet_clinic_user vet_clinic_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Uploads backup
docker compose exec backend tar czf - /app/uploads > $BACKUP_DIR/uploads_$DATE.tar.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Make it executable and add to cron:
```bash
chmod +x backup.sh
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Updates

**Update Docker images:**
```bash
# Pull latest base images
docker compose pull

# Rebuild with new images
docker compose up -d --build
```

**Update application code:**
```bash
git pull
docker compose up -d --build
```

### Monitoring

**Health checks:**
```bash
# Check all services
docker compose ps

# Test health endpoints
curl http://localhost:5000/api/health
curl http://localhost/
```

**Resource monitoring:**
```bash
# Real-time stats
docker stats

# Detailed container info
docker compose exec backend top
```

## Advanced Topics

### Custom Network Configuration

Edit `docker-compose.yml` to customize network settings:

```yaml
networks:
  lch-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Using External Database

To use an external PostgreSQL:

```yaml
# In docker-compose.yml, remove the postgres service
# Update backend environment:
environment:
  DATABASE_URL: postgresql://user:pass@external-host:5432/dbname
```

### Adding Redis Cache

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - lch-network
```

## Support

For issues or questions:

1. Check the logs: `docker compose logs`
2. Review this guide's troubleshooting section
3. Check the main [README.md](./README.md)
4. Open an issue on GitHub

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Nginx Docker Image](https://hub.docker.com/_/nginx)
- [Application README](./README.md)

---

**Happy Deploying! 🐱**

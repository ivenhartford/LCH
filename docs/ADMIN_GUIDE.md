# Lenox Cat Hospital - Administrator Guide

**Comprehensive System Administration Manual** | Last Updated: 2025-11-07

This guide provides detailed instructions for system administrators managing the Lenox Cat Hospital Practice Management System.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Installation & Deployment](#installation--deployment)
3. [Configuration Management](#configuration-management)
4. [User & Permission Management](#user--permission-management)
5. [Database Administration](#database-administration)
6. [Backup & Recovery](#backup--recovery)
7. [Security Hardening](#security-hardening)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Scaling & Performance](#scaling--performance)
10. [Troubleshooting](#troubleshooting)
11. [Disaster Recovery](#disaster-recovery)

---

## System Architecture

### Components

The Lenox Cat Hospital system consists of four main Docker containers:

1. **PostgreSQL Database** (`postgres`)
   - Stores all application data
   - Version: PostgreSQL 15 Alpine
   - Data persistence via Docker volume
   - Health checks enabled

2. **Flask Backend API** (`backend`)
   - Python 3.11 with Flask framework
   - Gunicorn WSGI server (production)
   - RESTful API endpoints
   - Database migrations with Flask-Migrate
   - Automatic health checks

3. **React Frontend** (`frontend`)
   - Node.js 18/20 for building
   - Nginx Alpine for serving
   - Material-UI components
   - Proxies API requests to backend

4. **Certbot** (`certbot`) - Production only
   - Manages SSL certificates
   - Automatic renewal
   - Let's Encrypt integration

5. **Backup Service** (`backup`) - Production only
   - Automated daily database backups
   - Configurable retention period
   - Compressed backups

### Network Architecture

```
Internet
    |
    v
[Nginx - Port 80/443]
    |
    +---> /api/* ----> [Backend - Port 5000] ---> [PostgreSQL - Port 5432]
    |
    +---> /* --------> [Frontend Static Files]
```

**Production with SSL:**
```
Internet (Port 443)
    |
    v
[Nginx with SSL]
    |
    +---> HTTPS terminated
    +---> /api/* ----> Backend (internal)
    +---> /* --------> Frontend SPA
```

### Data Storage

**Docker Volumes:**
- `lch-postgres-data` - PostgreSQL database files
- `lch-postgres-logs` - PostgreSQL logs (production)
- `lch-backend-logs` - Application logs (audit, performance, errors)
- `lch-backend-uploads` - User-uploaded files (patient photos, documents)
- `lch-backend-instance` - Flask instance folder (database in development)
- `lch-backups` - Database backup files

**Volume Locations:**
- Development: Local directory mounts
- Production: Named Docker volumes (persistent)

---

## Installation & Deployment

### Prerequisites

**Required Software:**
- Docker 20.10+ ([Installation Guide](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ ([Installation Guide](https://docs.docker.com/compose/install/))
- Git (for version control)

**System Requirements:**
- **Minimum:** 2 CPU cores, 4GB RAM, 20GB disk
- **Recommended:** 4 CPU cores, 8GB RAM, 100GB SSD
- **OS:** Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+, CentOS 8+)

**Network Requirements:**
- Port 80 (HTTP) - open to internet
- Port 443 (HTTPS) - open to internet (production)
- Port 5432 (PostgreSQL) - internal only (Docker network)
- Port 5000 (Backend) - internal only (Docker network)

### Initial Deployment

#### Step 1: Clone Repository

```bash
# Clone from Git repository
git clone https://github.com/yourusername/LCH.git
cd LCH

# Or if deploying from a release archive
tar -xzf lch-v1.0.0.tar.gz
cd LCH
```

#### Step 2: Configure Environment

```bash
# Copy production template
cp .env.production .env

# Edit configuration
nano .env
```

**Required Configuration:**

```bash
# === CRITICAL SECURITY SETTINGS ===

# Generate with: openssl rand -hex 32
SECRET_KEY=<YOUR-SECRET-KEY-HERE>

# Strong password for PostgreSQL
POSTGRES_PASSWORD=<YOUR-POSTGRES-PASSWORD>

# === PRODUCTION DOMAIN (for SSL) ===
DOMAIN_NAME=clinic.example.com
SSL_EMAIL=admin@example.com

# === DATABASE CONFIGURATION ===
POSTGRES_DB=vet_clinic_db
POSTGRES_USER=vet_clinic_user
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# === APPLICATION SETTINGS ===
FLASK_ENV=production
FLASK_DEBUG=false
LOG_LEVEL=INFO

# Session security (HTTPS only)
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# === GUNICORN (Backend Server) ===
GUNICORN_WORKERS=4  # CPU cores * 2 + 1
GUNICORN_TIMEOUT=120
GUNICORN_WORKER_CLASS=sync

# === CORS (Frontend Domain) ===
CORS_ORIGINS=https://clinic.example.com

# === BACKUP CONFIGURATION ===
BACKUP_RETENTION_DAYS=30

# === INITIAL ADMIN USER (Optional) ===
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=temporary-password-CHANGE-THIS
INITIAL_ADMIN_ROLE=administrator
```

**Security Best Practices:**
- Never use default values in production
- Use strong, unique passwords (20+ characters)
- Store `.env` file securely (chmod 600)
- Use a password manager for credentials

#### Step 3: Deploy Application

**Without SSL (Development/Testing):**

```bash
./scripts/deploy.sh development
```

**With SSL (Production):**

```bash
# First, ensure your domain points to your server
# Verify DNS: dig +short clinic.example.com

# Deploy with SSL
./scripts/deploy.sh production

# Initialize SSL certificates
./scripts/init-ssl.sh
```

#### Step 4: Verify Deployment

```bash
# Check all services are healthy
docker-compose ps

# Should show:
# NAME         STATUS                PORTS
# lch-postgres   Up (healthy)          5432/tcp
# lch-backend    Up (healthy)          5000/tcp
# lch-frontend   Up                    0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp

# Test backend health
curl http://localhost:5000/api/health

# Test frontend (replace with your domain in production)
curl http://localhost/
```

#### Step 5: Create Initial Admin User

**Method 1: Using environment variables (recommended for automation)**

Set these in `.env` before deployment:

```bash
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=temporary-secure-password
```

**Method 2: Manually after deployment**

```bash
# Access backend container
docker-compose exec backend flask shell

# In Flask shell:
from app import db
from app.models import User

admin = User(username='admin', role='administrator')
admin.set_password('your-secure-password')
db.session.add(admin)
db.session.commit()
exit()
```

⚠️ **CRITICAL:** Change the initial admin password immediately after first login!

---

## Configuration Management

### Environment Variables Reference

#### Security Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ Yes | None | Flask secret key for sessions (use `openssl rand -hex 32`) |
| `POSTGRES_PASSWORD` | ✅ Yes | None | PostgreSQL database password |
| `SESSION_COOKIE_SECURE` | No | false | Require HTTPS for session cookies (true in production) |
| `SESSION_COOKIE_HTTPONLY` | No | true | Prevent JavaScript access to cookies |
| `CORS_ORIGINS` | No | http://localhost | Allowed origins for CORS |

#### Database Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_DB` | No | vet_clinic_db | Database name |
| `POSTGRES_USER` | No | vet_clinic_user | Database username |
| `POSTGRES_HOST` | No | postgres | Database hostname |
| `POSTGRES_PORT` | No | 5432 | Database port |
| `DATABASE_URL` | No | Auto-generated | Full connection string |

#### Application Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_ENV` | No | production | Flask environment (production/development) |
| `FLASK_DEBUG` | No | false | Enable debug mode (never true in production!) |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |

#### Gunicorn Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GUNICORN_WORKERS` | No | 4 | Number of worker processes |
| `GUNICORN_TIMEOUT` | No | 120 | Worker timeout in seconds |
| `GUNICORN_WORKER_CLASS` | No | sync | Worker class (sync/gevent/eventlet) |
| `GUNICORN_MAX_REQUESTS` | No | 1000 | Max requests before worker restart |

#### Backup Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKUP_RETENTION_DAYS` | No | 30 | Days to keep backups |
| `BACKUP_DIR` | No | /backups | Backup storage directory |

### Updating Configuration

**After changing `.env` file:**

```bash
# Restart services to apply changes
docker-compose restart

# Or for full reload
docker-compose down
docker-compose up -d
```

**⚠️ Changing database credentials requires manual intervention:**

```bash
# 1. Stop all services
docker-compose down

# 2. Update .env file with new credentials

# 3. Update database password
docker-compose up -d postgres
docker-compose exec postgres psql -U postgres -c "ALTER USER vet_clinic_user PASSWORD 'new-password';"

# 4. Restart all services
docker-compose down
docker-compose up -d
```

---

## User & Permission Management

### User Roles

The system supports role-based access control (RBAC):

| Role | Access Level | Permissions |
|------|-------------|-------------|
| **Administrator** | Full System | All operations, user management, system settings |
| **Veterinarian** | Clinical + Billing | Diagnose, prescribe, access medical records, billing |
| **Technician** | Clinical | Assist with exams, limited prescriptions, lab results |
| **Receptionist** | Front Desk | Appointments, client management, basic invoicing |

### Creating Staff Users

#### Via Web Interface (Recommended)

1. Log in as Administrator
2. Navigate to **Staff Management** → **Staff**
3. Click **Add Staff Member**
4. Fill in required fields:
   - Personal Information (name, email, phone)
   - Professional Information (role, license number)
   - Permissions:
     - `can_prescribe` - Can write prescriptions
     - `can_perform_surgery` - Can perform surgical procedures
     - `can_access_billing` - Can view financial data
5. Set username and temporary password
6. Click **Save**

#### Via Command Line

```bash
# Access backend container
docker-compose exec backend flask shell

# Create user
from app import db
from app.models import User

# Create veterinarian
vet = User(
    username='dr_smith',
    role='veterinarian',
    can_prescribe=True,
    can_perform_surgery=True,
    can_access_billing=True
)
vet.set_password('temporary-password')
db.session.add(vet)
db.session.commit()

# Create receptionist
receptionist = User(
    username='jane_doe',
    role='receptionist',
    can_prescribe=False,
    can_perform_surgery=False,
    can_access_billing=True
)
receptionist.set_password('temporary-password')
db.session.add(receptionist)
db.session.commit()
```

### Disabling/Deleting Users

**Disable a user (recommended):**

```bash
docker-compose exec backend flask shell

from app import db
from app.models import User

user = User.query.filter_by(username='username_to_disable').first()
user.status = 'inactive'
db.session.commit()
```

**Delete a user (permanent):**

```bash
# Only do this if absolutely necessary
# All associated audit logs will remain but user record is deleted

docker-compose exec backend flask shell

from app import db
from app.models import User

user = User.query.filter_by(username='username_to_delete').first()
db.session.delete(user)
db.session.commit()
```

### Password Management

**Reset User Password:**

```bash
docker-compose exec backend flask shell

from app import db
from app.models import User

user = User.query.filter_by(username='username').first()
user.set_password('new-temporary-password')
db.session.commit()

print(f"Password reset for {user.username}")
print("User should change password on next login")
```

**Password Requirements:**
- Minimum 8 characters
- Must contain: uppercase, lowercase, digit, special character
- Passwords are hashed with bcrypt (cost factor 12)
- No password history (can be implemented if needed)

### Account Lockout

The system automatically locks accounts after 5 failed login attempts for 15 minutes.

**Manually unlock an account:**

```bash
docker-compose exec backend flask shell

from app import db
from app.models import User

user = User.query.filter_by(username='locked_username').first()
user.failed_login_attempts = 0
user.account_locked_until = None
db.session.commit()

print(f"Account unlocked for {user.username}")
```

---

## Database Administration

### Database Access

**Access PostgreSQL shell:**

```bash
# Using docker-compose
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db

# Common queries
\dt              # List tables
\d+ table_name   # Describe table
SELECT COUNT(*) FROM users;
```

**Execute SQL from file:**

```bash
docker-compose exec -T postgres psql -U vet_clinic_user -d vet_clinic_db < query.sql
```

### Database Migrations

The application uses Flask-Migrate (Alembic) for schema management.

**Create a new migration:**

```bash
# After modifying models.py
docker-compose exec backend flask db migrate -m "Description of changes"

# Review the generated migration file
docker-compose exec backend cat migrations/versions/XXXX_description.py

# Apply the migration
docker-compose exec backend flask db upgrade
```

**Rollback a migration:**

```bash
# Downgrade one revision
docker-compose exec backend flask db downgrade

# Downgrade to specific revision
docker-compose exec backend flask db downgrade <revision_id>
```

**View migration history:**

```bash
docker-compose exec backend flask db history
docker-compose exec backend flask db current
```

### Database Maintenance

**Vacuum and analyze (improve performance):**

```bash
# Full vacuum (requires downtime)
docker-compose exec postgres vacuumdb -U vet_clinic_user -d vet_clinic_db --full --analyze

# Regular vacuum (no downtime)
docker-compose exec postgres vacuumdb -U vet_clinic_user -d vet_clinic_db --analyze
```

**Reindex database:**

```bash
docker-compose exec postgres reindexdb -U vet_clinic_user -d vet_clinic_db
```

**Check database size:**

```bash
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'vet_clinic_db';"
```

**Check table sizes:**

```bash
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

---

## Backup & Recovery

### Automated Backups

Backups run automatically at 2 AM daily (configured in `docker-compose.prod.yml`).

**Backup Configuration:**
- **Frequency:** Daily (2 AM)
- **Retention:** 30 days (configurable via `BACKUP_RETENTION_DAYS`)
- **Format:** Compressed SQL dump (gzip)
- **Location:** `/backups` Docker volume

**View backup status:**

```bash
# List all backups
./scripts/list-backups.sh

# Check backup container logs
docker-compose logs backup
```

### Manual Backup

**Create immediate backup:**

```bash
./scripts/backup.sh

# Or via Docker
docker-compose exec postgres /backup.sh
```

**Backup with custom name:**

```bash
export BACKUP_DIR=/path/to/backups
export BACKUP_FILE=my_backup_$(date +%Y%m%d).sql.gz
./scripts/backup.sh
```

### Backup Verification

**Verify backup integrity:**

```bash
# Test gzip integrity
gunzip -t /path/to/backup.sql.gz

# Restore to a test database
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE test_restore;"
gunzip -c backup.sql.gz | docker-compose exec -T postgres psql -U vet_clinic_user -d test_restore
docker-compose exec postgres psql -U postgres -c "DROP DATABASE test_restore;"
```

### Restore from Backup

**⚠️ WARNING:** This will replace the current database!

```bash
# List available backups
./scripts/list-backups.sh

# Restore from specific backup
./scripts/restore.sh backup_vet_clinic_db_20250107_140000.sql.gz

# Restore creates a pre-restore backup automatically
```

**Manual restore process:**

```bash
# 1. Stop backend to prevent new connections
docker-compose stop backend

# 2. Drop and recreate database
docker-compose exec postgres psql -U postgres <<EOF
DROP DATABASE vet_clinic_db;
CREATE DATABASE vet_clinic_db OWNER vet_clinic_user;
EOF

# 3. Restore from backup
gunzip -c /path/to/backup.sql.gz | docker-compose exec -T postgres psql -U vet_clinic_user -d vet_clinic_db

# 4. Restart backend
docker-compose start backend
```

### Off-site Backups

**For production, configure off-site backups:**

```bash
# Option 1: Rsync to remote server
rsync -avz --delete /var/lib/docker/volumes/lch-backups/ user@backup-server:/backups/lch/

# Option 2: Upload to S3
aws s3 sync /var/lib/docker/volumes/lch-backups/ s3://your-bucket/lch-backups/

# Option 3: Use cloud backup service (Duplicati, Restic, Borg)
```

**Automate off-site backups with cron:**

```bash
# Edit crontab
crontab -e

# Add daily off-site backup at 3 AM (after local backup completes)
0 3 * * * rsync -avz /var/lib/docker/volumes/lch-backups/ user@backup-server:/backups/lch/
```

---

## Security Hardening

### Security Checklist

Production systems should meet these security requirements:

**Critical:**
- [ ] Strong `SECRET_KEY` set (32+ characters, random)
- [ ] Strong database password (20+ characters)
- [ ] SSL/HTTPS enabled
- [ ] Initial admin password changed
- [ ] Firewall configured (only 80/443 open)
- [ ] `FLASK_DEBUG=false` in production
- [ ] `SESSION_COOKIE_SECURE=true` in production

**Important:**
- [ ] Regular security updates applied
- [ ] Audit logs enabled and monitored
- [ ] User passwords meet complexity requirements
- [ ] Failed login tracking enabled (automatic)
- [ ] Regular backups verified
- [ ] Off-site backups configured
- [ ] Database not directly accessible from internet

**Recommended:**
- [ ] Two-factor authentication (planned for Phase 6+)
- [ ] Intrusion detection system (IDS)
- [ ] Web application firewall (WAF)
- [ ] Log aggregation and monitoring (Splunk/ELK)
- [ ] Security scanning (OWASP ZAP, Nessus)

### Firewall Configuration

**Using UFW (Ubuntu):**

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (if remote)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Deny all other incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Check status
sudo ufw status verbose
```

**Using firewalld (RHEL/CentOS):**

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### SSL Certificate Management

**Certificate Renewal:**

Certificates automatically renew via the certbot container (checks twice daily).

**Manual renewal:**

```bash
docker-compose run --rm certbot renew
```

**View certificate details:**

```bash
docker-compose run --rm certbot certificates
```

**Certificate expires in 90 days.** Renewal typically happens 30 days before expiry.

### Security Monitoring

**View security events:**

```bash
# All security events
docker-compose exec backend cat /app/logs/security.log

# Failed login attempts
docker-compose exec backend grep "failed_login" /app/logs/security.log

# Brute force detection
docker-compose exec backend grep "brute_force" /app/logs/security.log

# Recent security events (last 100)
docker-compose exec backend tail -100 /app/logs/security.log
```

**Monitor failed logins:**

```bash
# Count failed logins by user
docker-compose exec backend grep "failed_login" /app/logs/security.log | \
  grep -oP 'username=\K[^,]+' | sort | uniq -c | sort -rn
```

---

## Monitoring & Maintenance

### Health Checks

**Service health status:**

```bash
# All services
docker-compose ps

# Individual service health
docker inspect --format='{{.State.Health.Status}}' lch-backend
docker inspect --format='{{.State.Health.Status}}' lch-postgres
```

**Application health endpoint:**

```bash
# Backend health
curl http://localhost:5000/api/health

# Response: {"status": "healthy", "database": "connected"}
```

### Log Management

**View logs:**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 backend

# Since specific time
docker-compose logs --since="2025-01-07T10:00:00" backend
```

**Log files location:**

```
/var/lib/docker/volumes/lch-backend-logs/_data/
├── app.log           # Application logs
├── audit.log         # Audit trail (WHO did WHAT and WHEN)
├── security.log      # Security events
└── performance.log   # Performance metrics
```

**Log rotation:**

Configure log rotation to prevent disk space issues:

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/lch

# Add configuration:
/var/lib/docker/volumes/lch-backend-logs/_data/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}

# Test configuration
sudo logrotate -d /etc/logrotate.d/lch

# Force rotation
sudo logrotate -f /etc/logrotate.d/lch
```

### Resource Monitoring

**Container resource usage:**

```bash
# Real-time stats
docker stats

# Output:
# CONTAINER     CPU %    MEM USAGE / LIMIT    MEM %    NET I/O
# lch-backend   2.5%     512MB / 2GB          25%      1.2GB / 800MB
# lch-postgres  1.8%     256MB / 2GB          12%      800MB / 1.2GB
# lch-frontend  0.1%     50MB / 512MB         10%      100MB / 200MB
```

**Disk usage:**

```bash
# Docker volumes
docker system df -v

# Specific volume
docker volume inspect lch-postgres-data | grep -A 10 Mountpoint
du -sh /var/lib/docker/volumes/lch-postgres-data/_data
```

**Database statistics:**

```bash
# Connection count
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT count(*) FROM pg_stat_activity WHERE datname = 'vet_clinic_db';"

# Slow queries (queries taking > 1 second)
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '1 second';"

# Cache hit ratio (should be > 99%)
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit)  as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;"
```

### Performance Tuning

**For High-Traffic Clinics (50+ concurrent users):**

Edit `.env`:

```bash
# Increase Gunicorn workers
GUNICORN_WORKERS=8  # 2 * CPU_CORES + 1

# Increase timeout
GUNICORN_TIMEOUT=180

# Use gevent worker for better concurrency
GUNICORN_WORKER_CLASS=gevent
```

Edit `docker-compose.prod.yml` to increase resources:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 4G
      reservations:
        cpus: '2'
        memory: 2G

postgres:
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 4G
      reservations:
        cpus: '2'
        memory: 2G
```

**PostgreSQL tuning:**

```bash
# Edit PostgreSQL configuration
docker-compose exec postgres bash

# Edit postgresql.conf
nano /var/lib/postgresql/data/postgresql.conf

# Recommended changes for production:
shared_buffers = 1GB              # 25% of system RAM
effective_cache_size = 3GB        # 75% of system RAM
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1           # For SSD
effective_io_concurrency = 200   # For SSD
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
```

---

## Scaling & Performance

### Horizontal Scaling

**Scale backend workers:**

```bash
# Increase backend instances
docker-compose up -d --scale backend=3

# With load balancer (requires nginx configuration)
```

### Vertical Scaling

**Increase container resources:**

Edit `docker-compose.prod.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'      # Increase from 2
          memory: 4G     # Increase from 2G
```

### Database Optimization

**Already implemented:**
- 60+ database indexes on all major tables
- Foreign key indexes for JOINs
- Composite indexes for common queries

**Check index usage:**

```bash
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC
LIMIT 20;"
```

**Unused indexes (consider removing):**

```bash
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;"
```

---

## Troubleshooting

### Common Issues

#### Issue: Container won't start

**Diagnosis:**

```bash
# Check container logs
docker-compose logs backend

# Check container status
docker-compose ps

# Inspect container
docker inspect lch-backend
```

**Solutions:**

```bash
# Rebuild container
docker-compose build backend
docker-compose up -d backend

# Remove and recreate
docker-compose rm -f backend
docker-compose up -d backend
```

#### Issue: Database connection failed

**Diagnosis:**

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec backend python -c "
from app import create_app
app = create_app()
with app.app_context():
    from app import db
    print('Database connection:', db.engine.url)
"
```

**Solutions:**

```bash
# Verify credentials in .env
cat .env | grep POSTGRES

# Restart PostgreSQL
docker-compose restart postgres

# Wait for PostgreSQL to be ready
docker-compose logs -f postgres
# Wait for: "database system is ready to accept connections"
```

#### Issue: SSL certificate errors

**Diagnosis:**

```bash
# Check certificate status
docker-compose run --rm certbot certificates

# Test SSL connection
openssl s_client -connect clinic.example.com:443 -servername clinic.example.com
```

**Solutions:**

```bash
# Renew certificate
docker-compose run --rm certbot renew

# Force renewal
docker-compose run --rm certbot renew --force-renewal

# Re-initialize SSL
./scripts/init-ssl.sh
```

#### Issue: High CPU/memory usage

**Diagnosis:**

```bash
# Check resource usage
docker stats

# Check process list in container
docker-compose exec backend top

# Check slow queries
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT pid, query_start, state, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;"
```

**Solutions:**

```bash
# Increase resources in docker-compose.prod.yml
# Restart workers more frequently
GUNICORN_MAX_REQUESTS=500  # in .env

# Optimize database
docker-compose exec postgres vacuumdb -U vet_clinic_user -d vet_clinic_db --analyze

# Clear old logs
./scripts/cleanup-logs.sh  # (create if needed)
```

#### Issue: Disk space full

**Diagnosis:**

```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df -v

# Check volume sizes
docker volume ls -q | xargs docker volume inspect | grep -A 5 Mountpoint | grep -E 'Mountpoint|Name'
for vol in $(docker volume ls -q); do
    echo "$vol: $(sudo du -sh /var/lib/docker/volumes/$vol/_data | cut -f1)"
done
```

**Solutions:**

```bash
# Remove old Docker images
docker image prune -a

# Remove unused volumes
docker volume prune

# Clean old backups (older than retention period)
./scripts/list-backups.sh  # Check current backups
# Manually remove old backups if needed

# Clean logs
sudo truncate -s 0 /var/lib/docker/volumes/lch-backend-logs/_data/*.log
```

### Emergency Procedures

#### Complete System Reset

**⚠️ This will DELETE ALL DATA!**

```bash
# Stop all services
docker-compose down

# Remove all volumes (DATA LOSS!)
docker volume rm lch-postgres-data lch-backend-logs lch-backend-uploads lch-backend-instance lch-backups

# Restart from scratch
./scripts/deploy.sh production
```

#### Restore from Catastrophic Failure

See [Disaster Recovery](#disaster-recovery) section.

---

## Disaster Recovery

### Disaster Recovery Plan

**Recovery Time Objective (RTO):** < 4 hours
**Recovery Point Objective (RPO):** < 24 hours (daily backups)

### Scenario 1: Database Corruption

**Recovery Steps:**

```bash
# 1. Stop backend
docker-compose stop backend

# 2. Create emergency backup of current state
docker-compose exec postgres pg_dump -U vet_clinic_user vet_clinic_db | gzip > emergency_backup.sql.gz

# 3. Restore from latest backup
./scripts/restore.sh $(./scripts/list-backups.sh | grep "backup_" | tail -1 | awk '{print $1}')

# 4. Verify restoration
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "SELECT COUNT(*) FROM users;"

# 5. Restart backend
docker-compose start backend
```

### Scenario 2: Complete Server Failure

**Requirements:**
- Off-site backups (S3, remote server, etc.)
- New server with Docker installed
- Copy of `.env` file (stored securely off-site)

**Recovery Steps:**

```bash
# 1. On new server, install Docker and Docker Compose
# See installation instructions above

# 2. Clone repository
git clone https://github.com/yourusername/LCH.git
cd LCH

# 3. Restore .env file
# Copy from secure backup location

# 4. Download latest backup from off-site location
aws s3 cp s3://your-bucket/lch-backups/backup_latest.sql.gz ./

# Or from remote server
scp user@backup-server:/backups/lch/backup_latest.sql.gz ./

# 5. Deploy application
./scripts/deploy.sh production

# 6. Restore database
./scripts/restore.sh backup_latest.sql.gz

# 7. Reinitialize SSL (if using Let's Encrypt)
./scripts/init-ssl.sh

# 8. Verify all services
docker-compose ps
curl https://clinic.example.com/api/health
```

### Scenario 3: Accidental Data Deletion

**Recovery Steps:**

```bash
# 1. Immediately stop all services to prevent further changes
docker-compose stop backend frontend

# 2. Identify the last good backup before the deletion
./scripts/list-backups.sh

# 3. Restore from that backup
./scripts/restore.sh backup_vet_clinic_db_YYYYMMDD_HHMMSS.sql.gz

# 4. Restart services
docker-compose start backend frontend

# 5. Verify data restoration
# Log in and check if deleted data is present
```

### Disaster Recovery Testing

**Conduct quarterly DR tests:**

```bash
# 1. Create test environment
cp .env .env.dr-test
# Modify to use different ports and database names

# 2. Deploy test environment
COMPOSE_PROJECT_NAME=lch-dr-test docker-compose -f docker-compose.yml up -d

# 3. Restore latest backup to test environment
POSTGRES_HOST=localhost POSTGRES_PORT=5433 ./scripts/restore.sh backup_latest.sql.gz

# 4. Verify restoration
# Check data integrity, application functionality

# 5. Cleanup test environment
docker-compose -p lch-dr-test down -v
```

### Backup Verification Schedule

**Weekly:**
- Verify backups are being created (check dates)
- Check backup file integrity (gunzip -t)

**Monthly:**
- Restore backup to test environment
- Verify data completeness
- Document any issues

**Quarterly:**
- Full disaster recovery test
- Update DR procedures
- Review and update RTO/RPO

---

## Appendix

### Useful Commands Reference

**Docker Compose:**

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend bash
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db

# Scale a service
docker-compose up -d --scale backend=3

# Rebuild and restart
docker-compose build backend && docker-compose up -d backend
```

**Database:**

```bash
# Backup
./scripts/backup.sh

# Restore
./scripts/restore.sh backup_file.sql.gz

# Access database
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db

# Run SQL file
docker-compose exec -T postgres psql -U vet_clinic_user -d vet_clinic_db < query.sql
```

**Logs:**

```bash
# Application logs
docker-compose exec backend cat /app/logs/app.log

# Audit logs
docker-compose exec backend cat /app/logs/audit.log

# Security logs
docker-compose exec backend cat /app/logs/security.log

# Performance logs
docker-compose exec backend cat /app/logs/performance.log
```

### Support & Resources

**Documentation:**
- User Guide: [USER_GUIDE.md](./USER_GUIDE.md)
- Quick Start: [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md)
- Docker Guide: [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)
- Security: [SECURITY.md](./SECURITY.md)

**External Resources:**
- Docker Documentation: https://docs.docker.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Flask Documentation: https://flask.palletsprojects.com/
- nginx Documentation: https://nginx.org/en/docs/

---

**Document Version:** 1.0
**Last Updated:** 2025-11-07
**Maintained By:** System Administration Team

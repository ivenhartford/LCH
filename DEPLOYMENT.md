# Lenox Cat Hospital - Production Deployment Guide

**Last Updated:** 2025-11-05
**Version:** 1.0
**Target Environment:** Production (Linux/Ubuntu)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Database Setup](#database-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Environment Variables](#environment-variables)
8. [Process Management](#process-management)
9. [Monitoring & Logging](#monitoring--logging)
10. [Backup Strategy](#backup-strategy)
11. [Security Checklist](#security-checklist)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Server Requirements

**Minimum Specifications:**
- **OS:** Ubuntu 20.04 LTS or later (or equivalent Linux distribution)
- **CPU:** 2 cores
- **RAM:** 4GB
- **Storage:** 20GB SSD
- **Network:** Static IP address with open ports 80, 443

**Recommended Specifications:**
- **CPU:** 4 cores
- **RAM:** 8GB
- **Storage:** 50GB SSD
- **Network:** Load balancer for high availability

### Software Requirements

- Python 3.11+
- Node.js 16+ and npm
- PostgreSQL 14+
- Nginx
- Git
- SSL certificate (Let's Encrypt recommended)

---

## Server Setup

### 1. Update System Packages

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Required Packages

```bash
# Install Python and pip
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Nginx
sudo apt install -y nginx

# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Git
sudo apt install -y git

# Install Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
```

### 3. Create Application User

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash lchapp
sudo usermod -aG sudo lchapp

# Switch to the application user
sudo su - lchapp
```

---

## Database Setup

### 1. Create PostgreSQL Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE lenox_cat_hospital;
CREATE USER lchapp WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE lenox_cat_hospital TO lchapp;
ALTER DATABASE lenox_cat_hospital OWNER TO lchapp;
\q
```

### 2. Configure PostgreSQL for Remote Access (if needed)

Edit `/etc/postgresql/14/main/postgresql.conf`:
```conf
listen_addresses = 'localhost'  # Keep localhost for security
```

Edit `/etc/postgresql/14/main/pg_hba.conf`:
```conf
# Add this line for local connections
local   lenox_cat_hospital   lchapp   md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 3. Test Database Connection

```bash
psql -U lchapp -d lenox_cat_hospital -h localhost
```

---

## Backend Deployment

### 1. Clone Repository

```bash
# As lchapp user
cd /home/lchapp
git clone https://github.com/yourusername/LCH.git
cd LCH
```

### 2. Set Up Python Virtual Environment

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

### 4. Configure Environment Variables

Create `/home/lchapp/LCH/backend/.env`:

```bash
# Flask Configuration
FLASK_APP=app:create_app
FLASK_ENV=production
SECRET_KEY=your_very_long_random_secret_key_here_use_at_least_32_characters

# Database Configuration
DATABASE_URL=postgresql://lchapp:your_secure_password_here@localhost/lenox_cat_hospital

# CORS Configuration (update with your domain)
CORS_ORIGINS=https://yourdomain.com

# Security Settings
SECURITY_PASSWORD_SALT=another_random_salt_string_here
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://

# Email Configuration (for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_specific_password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# JWT Configuration
JWT_SECRET_KEY=yet_another_random_secret_key_for_jwt
JWT_ACCESS_TOKEN_EXPIRES=86400  # 24 hours in seconds
```

**Generate Secure Secret Keys:**
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

### 5. Run Database Migrations

```bash
source venv/bin/activate
flask db upgrade
```

### 6. Create Admin User

```bash
flask shell
```

In Flask shell:
```python
from app import db
from app.models import User

admin = User(
    username='admin',
    email='admin@lenoxcathospital.com',
    role='administrator',
    first_name='System',
    last_name='Administrator'
)
admin.set_password('YourSecurePassword123!')
db.session.add(admin)
db.session.commit()
print(f"Admin user created: {admin.username}")
exit()
```

### 7. Test Backend

```bash
gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"
```

Test at: `curl http://localhost:5000/api/check_session`

---

## Frontend Deployment

### 1. Install Frontend Dependencies

```bash
cd /home/lchapp/LCH/frontend
npm install
```

### 2. Configure Frontend Environment

Create `/home/lchapp/LCH/frontend/.env.production`:

```bash
# API Configuration
REACT_APP_API_URL=https://yourdomain.com

# Logging
REACT_APP_LOG_LEVEL=WARN
REACT_APP_LOG_TO_BACKEND=true

# Performance Monitoring
REACT_APP_ENABLE_PERFORMANCE_MONITORING=true
```

### 3. Build Frontend for Production

```bash
npm run build
```

This creates an optimized production build in `frontend/build/`.

### 4. Verify Build

```bash
ls -lh frontend/build/
# Should see: index.html, static/ directory, manifest.json, etc.
```

---

## Nginx Configuration

### 1. Create Nginx Configuration

Create `/etc/nginx/sites-available/lenox-cat-hospital`:

```nginx
# Upstream for backend API
upstream backend_api {
    server 127.0.0.1:5000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration (Certbot will add these)
    # ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Root directory for frontend build
    root /home/lchapp/LCH/frontend/build;
    index index.html;

    # Client upload size (for document uploads)
    client_max_body_size 20M;

    # API proxy
    location /api/ {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Serve static files from frontend build
    location / {
        try_files $uri $uri/ /index.html;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Don't cache HTML
    location ~* \.(html)$ {
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate";
    }

    # Security: Hide sensitive files
    location ~ /\. {
        deny all;
    }

    # Logging
    access_log /var/log/nginx/lenox-cat-hospital-access.log;
    error_log /var/log/nginx/lenox-cat-hospital-error.log;
}
```

### 2. Enable Site Configuration

```bash
sudo ln -s /etc/nginx/sites-available/lenox-cat-hospital /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

---

## SSL/TLS Configuration

### 1. Obtain SSL Certificate with Let's Encrypt

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts to configure automatic HTTPS redirection.

### 2. Set Up Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically creates a cron job for renewal
# Verify it exists
sudo systemctl status certbot.timer
```

---

## Process Management

### 1. Create Systemd Service for Backend

Create `/etc/systemd/system/lenox-cat-hospital.service`:

```ini
[Unit]
Description=Lenox Cat Hospital Backend API
After=network.target postgresql.service

[Service]
Type=notify
User=lchapp
Group=lchapp
WorkingDirectory=/home/lchapp/LCH/backend
Environment="PATH=/home/lchapp/LCH/backend/venv/bin"
ExecStart=/home/lchapp/LCH/backend/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile /home/lchapp/LCH/backend/logs/gunicorn-access.log \
    --error-logfile /home/lchapp/LCH/backend/logs/gunicorn-error.log \
    --log-level info \
    "app:create_app()"

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
# Create logs directory
sudo mkdir -p /home/lchapp/LCH/backend/logs
sudo chown -R lchapp:lchapp /home/lchapp/LCH/backend/logs

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable lenox-cat-hospital
sudo systemctl start lenox-cat-hospital

# Check status
sudo systemctl status lenox-cat-hospital
```

### 3. Service Management Commands

```bash
# Start service
sudo systemctl start lenox-cat-hospital

# Stop service
sudo systemctl stop lenox-cat-hospital

# Restart service
sudo systemctl restart lenox-cat-hospital

# View logs
sudo journalctl -u lenox-cat-hospital -f

# Check service status
sudo systemctl status lenox-cat-hospital
```

---

## Monitoring & Logging

### 1. Application Logs

**Backend Logs:**
- Application log: `/home/lchapp/LCH/backend/logs/vet_clinic.log`
- Gunicorn access: `/home/lchapp/LCH/backend/logs/gunicorn-access.log`
- Gunicorn error: `/home/lchapp/LCH/backend/logs/gunicorn-error.log`
- System logs: `journalctl -u lenox-cat-hospital`

**Nginx Logs:**
- Access log: `/var/log/nginx/lenox-cat-hospital-access.log`
- Error log: `/var/log/nginx/lenox-cat-hospital-error.log`

**PostgreSQL Logs:**
- `/var/log/postgresql/postgresql-14-main.log`

### 2. Log Rotation

Create `/etc/logrotate.d/lenox-cat-hospital`:

```
/home/lchapp/LCH/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    sharedscripts
    postrotate
        systemctl reload lenox-cat-hospital > /dev/null 2>&1 || true
    endscript
}
```

### 3. Monitoring Setup (Optional but Recommended)

**Install monitoring tools:**
```bash
# Prometheus Node Exporter
sudo apt install -y prometheus-node-exporter

# Install monitoring agent (choose one):
# - Datadog Agent
# - New Relic Agent
# - Sentry for error tracking
```

---

## Backup Strategy

### 1. Database Backups

Create backup script `/home/lchapp/backup-database.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/lchapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/lenox_cat_hospital_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U lchapp lenox_cat_hospital | gzip > $BACKUP_FILE

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup created: $BACKUP_FILE"
```

Make executable:
```bash
chmod +x /home/lchapp/backup-database.sh
```

### 2. Set Up Automated Backups

```bash
# Add to crontab
crontab -e

# Add this line (daily backup at 2 AM):
0 2 * * * /home/lchapp/backup-database.sh >> /home/lchapp/backup.log 2>&1
```

### 3. Document Backups

Create backup script for uploaded documents:

```bash
#!/bin/bash
BACKUP_DIR="/home/lchapp/backups/documents"
DATE=$(date +%Y%m%d_%H%M%S)
DOCUMENTS_DIR="/home/lchapp/LCH/backend/uploads"

mkdir -p $BACKUP_DIR

# Sync documents
rsync -av --delete $DOCUMENTS_DIR/ $BACKUP_DIR/latest/

# Create compressed archive
tar -czf "$BACKUP_DIR/documents_$DATE.tar.gz" -C $BACKUP_DIR latest/

# Keep only last 30 days
find $BACKUP_DIR -name "documents_*.tar.gz" -mtime +30 -delete

echo "Document backup created: $BACKUP_DIR/documents_$DATE.tar.gz"
```

### 4. Off-Site Backups (Highly Recommended)

```bash
# Set up automated S3 backups (AWS CLI required)
aws s3 sync /home/lchapp/backups/ s3://your-backup-bucket/lenox-cat-hospital/

# Or use rsync to remote server
rsync -avz /home/lchapp/backups/ user@backup-server:/backups/lenox-cat-hospital/
```

---

## Security Checklist

### Pre-Deployment Security

- [ ] All secret keys are randomly generated (32+ characters)
- [ ] SECRET_KEY is set in production environment
- [ ] Database password is strong and unique
- [ ] CORS_ORIGINS is set to production domain only
- [ ] SSL certificate is installed and valid
- [ ] HTTPS redirect is configured
- [ ] Security headers are enabled in Nginx
- [ ] Rate limiting is configured
- [ ] CSRF protection is enabled
- [ ] Session cookies are secure (HttpOnly, Secure flags)
- [ ] File upload size limits are set
- [ ] PostgreSQL only accepts local connections
- [ ] Default admin password has been changed
- [ ] Unnecessary ports are closed (firewall configured)
- [ ] Server OS is up to date
- [ ] Automated security updates are enabled

### Post-Deployment Security

```bash
# Enable UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Enable automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Install fail2ban for intrusion prevention
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## Environment Variables

### Required Production Environment Variables

**Backend (.env):**
```bash
# Critical - Must be set
FLASK_ENV=production
SECRET_KEY=<32+ character random string>
DATABASE_URL=postgresql://user:pass@localhost/dbname
CORS_ORIGINS=https://yourdomain.com

# Security
SECURITY_PASSWORD_SALT=<random string>
JWT_SECRET_KEY=<random string>
SESSION_COOKIE_SECURE=True

# Email (if using notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<your-email>
MAIL_PASSWORD=<app-password>
```

**Frontend (.env.production):**
```bash
REACT_APP_API_URL=https://yourdomain.com
REACT_APP_LOG_LEVEL=WARN
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Code is tested locally (97%+ test pass rate)
- [ ] All dependencies are up to date
- [ ] Database migrations are ready
- [ ] Environment variables are configured
- [ ] SSL certificates are obtained
- [ ] Backup strategy is in place
- [ ] Monitoring is configured

### Deployment Steps

- [ ] Pull latest code from repository
- [ ] Activate virtual environment
- [ ] Install/update dependencies
- [ ] Run database migrations
- [ ] Build frontend
- [ ] Test backend and frontend locally
- [ ] Update Nginx configuration
- [ ] Restart services
- [ ] Verify application is accessible
- [ ] Check logs for errors
- [ ] Test critical functionality
- [ ] Monitor performance for 24 hours

### Post-Deployment

- [ ] Verify SSL is working
- [ ] Test all major features
- [ ] Check database connections
- [ ] Verify backups are running
- [ ] Monitor error logs
- [ ] Set up alerts for critical issues
- [ ] Document any issues encountered
- [ ] Update deployment documentation

---

## Troubleshooting

### Common Issues

#### 1. Backend Service Won't Start

```bash
# Check service logs
sudo journalctl -u lenox-cat-hospital -n 50

# Check for port conflicts
sudo netstat -tulpn | grep 5000

# Verify environment variables
cat /home/lchapp/LCH/backend/.env

# Test manually
cd /home/lchapp/LCH/backend
source venv/bin/activate
gunicorn -w 1 -b 127.0.0.1:5000 "app:create_app()"
```

#### 2. Database Connection Issues

```bash
# Test database connection
psql -U lchapp -d lenox_cat_hospital -h localhost

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### 3. Frontend Not Loading

```bash
# Check Nginx configuration
sudo nginx -t

# Check Nginx is running
sudo systemctl status nginx

# Verify build directory exists
ls -la /home/lchapp/LCH/frontend/build/

# Check Nginx logs
sudo tail -f /var/log/nginx/lenox-cat-hospital-error.log
```

#### 4. 502 Bad Gateway

- Backend service is not running
- Backend is running on wrong port
- Nginx upstream configuration is incorrect

```bash
sudo systemctl status lenox-cat-hospital
curl http://localhost:5000/api/check_session
```

#### 5. SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate expiry
sudo certbot certificates

# Test SSL configuration
openssl s_client -connect yourdomain.com:443
```

---

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_patient_name ON patient(name);
CREATE INDEX IF NOT EXISTS idx_client_email ON client(email);
CREATE INDEX IF NOT EXISTS idx_appointment_date ON appointment(date);
CREATE INDEX IF NOT EXISTS idx_visit_date ON visit(date);
```

### Gunicorn Workers

Calculate optimal workers:
```
workers = (2 x CPU_cores) + 1
```

For 4 CPU cores: 9 workers

### Nginx Caching (Optional)

Add to Nginx configuration:
```nginx
# Cache static assets
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    # ... rest of proxy configuration
}
```

---

## Updates and Maintenance

### Updating the Application

```bash
# 1. Backup database
/home/lchapp/backup-database.sh

# 2. Pull latest code
cd /home/lchapp/LCH
git pull origin main

# 3. Update backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 4. Run migrations
flask db upgrade

# 5. Rebuild frontend
cd ../frontend
npm install
npm run build

# 6. Restart services
sudo systemctl restart lenox-cat-hospital
sudo systemctl reload nginx

# 7. Verify deployment
curl https://yourdomain.com/api/check_session
```

---

## Support and Contact

**Documentation:** See README.md and other project documentation files
**Issues:** Report bugs via project issue tracker
**Emergency Contacts:** [Add your support contacts here]

---

**Last Updated:** 2025-11-05
**Version:** 1.0

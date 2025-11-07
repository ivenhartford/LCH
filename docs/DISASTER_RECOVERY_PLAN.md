# Lenox Cat Hospital - Disaster Recovery Plan

**Version 1.0** | Last Updated: 2025-11-07 | Classification: CONFIDENTIAL

This document outlines the disaster recovery procedures for the Lenox Cat Hospital Practice Management System. It provides step-by-step instructions for recovering from various failure scenarios to ensure business continuity.

---

## Table of Contents

1. [Plan Overview](#plan-overview)
2. [Recovery Objectives](#recovery-objectives)
3. [Roles & Responsibilities](#roles--responsibilities)
4. [System Architecture](#system-architecture)
5. [Backup Strategy](#backup-strategy)
6. [Disaster Scenarios](#disaster-scenarios)
7. [Recovery Procedures](#recovery-procedures)
8. [Testing & Validation](#testing--validation)
9. [Contact Information](#contact-information)
10. [Document History](#document-history)

---

## Plan Overview

### Purpose

This Disaster Recovery (DR) Plan provides procedures to restore the Lenox Cat Hospital Practice Management System in the event of:
- Hardware failure
- Software corruption
- Data loss
- Natural disaster
- Cyber attack
- Human error

### Scope

This plan covers:
- PostgreSQL database
- Flask backend application
- React frontend application
- Docker infrastructure
- SSL certificates
- Application configurations
- User-uploaded files (patient photos, documents)
- Audit logs

### Plan Activation

This plan should be activated when:
- Production system is unavailable for > 30 minutes
- Data corruption is detected
- Security breach compromises data integrity
- System administrator declares a disaster

**Plan Owner:** IT Manager / System Administrator
**Review Frequency:** Quarterly
**Last Tested:** [To be completed during first DR test]

---

## Recovery Objectives

### Recovery Time Objective (RTO)

**Maximum tolerable downtime:** 4 hours

| Scenario | Target RTO |
|----------|-----------|
| Database corruption | 1 hour |
| Application failure | 30 minutes |
| Server hardware failure | 4 hours |
| Complete datacenter failure | 8 hours |
| Cyber attack | 24 hours |

### Recovery Point Objective (RPO)

**Maximum tolerable data loss:** 24 hours

| Data Type | RPO | Backup Frequency |
|-----------|-----|------------------|
| Database | 24 hours | Daily (2 AM) |
| Uploaded files | 24 hours | Daily (included in backup) |
| Audit logs | 24 hours | Daily (included in backup) |
| Configuration files | N/A | Version controlled (Git) |

### Service Level Targets

| Priority | Service | Recovery Order |
|----------|---------|----------------|
| P1 - Critical | Database | 1 |
| P1 - Critical | Backend API | 2 |
| P1 - Critical | Frontend UI | 3 |
| P2 - Important | SSL certificates | 4 |
| P3 - Normal | Monitoring | 5 |

---

## Roles & Responsibilities

### Disaster Recovery Team

| Role | Responsibilities | Contact |
|------|-----------------|---------|
| **DR Coordinator** | Declare disaster, coordinate recovery, communicate with stakeholders | [Name, Phone, Email] |
| **System Administrator** | Execute technical recovery procedures | [Name, Phone, Email] |
| **Database Administrator** | Database restoration and verification | [Name, Phone, Email] |
| **Application Owner** | Application testing and validation | [Name, Phone, Email] |
| **Network Administrator** | Network and firewall configuration | [Name, Phone, Email] |
| **Security Officer** | Security validation, incident response | [Name, Phone, Email] |
| **Business Owner** | Business validation, user notification | [Name, Phone, Email] |

### Escalation Path

1. **Level 1:** System Administrator (attempts recovery)
2. **Level 2:** DR Coordinator (declares disaster, activates plan)
3. **Level 3:** IT Manager (coordinates with vendors, external support)
4. **Level 4:** Executive Management (business decisions, public communication)

---

## System Architecture

### Production Environment

**Location:** [Specify: On-premises datacenter, AWS, DigitalOcean, etc.]
**Operating System:** Ubuntu 22.04 LTS
**Docker Version:** 24.0+
**Docker Compose Version:** 2.0+

### System Components

```
┌─────────────────────────────────────────┐
│         Internet (HTTPS/443)           │
└──────────────┬──────────────────────────┘
               │
     ┌─────────▼────────┐
     │  Nginx (Frontend) │  Port 80/443
     │  + SSL Termination │
     └─────────┬──────────┘
               │
     ┌─────────▼──────────┐
     │   Flask Backend    │  Port 5000 (internal)
     │   (Gunicorn)       │
     └─────────┬──────────┘
               │
     ┌─────────▼──────────┐
     │  PostgreSQL DB     │  Port 5432 (internal)
     └────────────────────┘
```

### Data Storage

| Component | Location | Backup Method |
|-----------|----------|---------------|
| Database | Docker volume: `lch-postgres-data` | pg_dump → gzip |
| Uploaded files | Docker volume: `lch-backend-uploads` | Included in file system backup |
| Application logs | Docker volume: `lch-backend-logs` | Included in file system backup |
| Backups | Docker volume: `lch-backups` | Replicated to off-site |

### Dependencies

- **DNS:** Domain registration and DNS provider
- **SSL Certificates:** Let's Encrypt (auto-renewing)
- **Email:** SMTP server (for notifications - Phase 6+)
- **Monitoring:** (Optional - to be implemented)

---

## Backup Strategy

### Automated Backups

**Schedule:** Daily at 2:00 AM local time

**Backup Process:**
1. Automated backup container wakes up
2. Executes `pg_dump` on PostgreSQL database
3. Compresses dump with gzip (compression level 6)
4. Stores in `/backups` volume
5. Creates metadata file with backup information
6. Deletes backups older than retention period (30 days)

**Backup Location (On-site):**
```
/var/lib/docker/volumes/lch-backups/_data/
├── backup_vet_clinic_db_20250107_020000.sql.gz
├── backup_vet_clinic_db_20250107_020000.meta
├── backup_vet_clinic_db_20250106_020000.sql.gz
├── backup_vet_clinic_db_20250106_020000.meta
└── ... (30 days retention)
```

### Off-Site Backups

**⚠️ CRITICAL:** Configure off-site backup replication!

**Recommended Options:**

**Option 1: Cloud Storage (S3/GCS/Azure Blob)**

```bash
# Install AWS CLI
apt-get install awscli

# Configure credentials
aws configure

# Sync backups to S3 (daily at 3 AM, after local backup)
0 3 * * * aws s3 sync /var/lib/docker/volumes/lch-backups/_data/ s3://lch-backups-offsite/ --exclude "*" --include "backup_*.sql.gz" --include "backup_*.meta"
```

**Option 2: Remote Server via rsync**

```bash
# Set up SSH key authentication
ssh-keygen -t ed25519
ssh-copy-id backup-user@backup-server.example.com

# Sync backups to remote server (daily at 3 AM)
0 3 * * * rsync -avz --delete /var/lib/docker/volumes/lch-backups/_data/ backup-user@backup-server.example.com:/backups/lch/
```

**Option 3: Backup Service (Duplicati, Restic, Borg)**

Choose a backup solution that supports:
- Encryption at rest
- Incremental backups
- Retention policies
- Multiple destinations

### Backup Verification

**Daily Automated Checks:**
- Verify backup file exists
- Verify gzip integrity (`gunzip -t`)
- Verify file size (> 100KB minimum)
- Log results to monitoring system

**Weekly Manual Checks:**
- List recent backups: `./scripts/list-backups.sh`
- Verify metadata files exist
- Check off-site replication status

**Monthly Restoration Tests:**
- Restore to test environment
- Verify table counts match production
- Test application functionality
- Document results

### Configuration Backups

**Git Repository:**
- All code in version control (GitHub/GitLab)
- `.env.example` files in repository
- Actual `.env` file stored securely (separate from code)

**Secure `.env` Storage:**
```bash
# Encrypt .env file for off-site storage
gpg --symmetric --cipher-algo AES256 .env
# Store .env.gpg in secure location (password manager, encrypted drive)

# Decrypt when needed
gpg -d .env.gpg > .env
```

---

## Disaster Scenarios

### Scenario 1: Database Corruption

**Symptoms:**
- Database connection errors
- Data inconsistency errors
- PostgreSQL crash logs
- Application errors related to database queries

**Likelihood:** Medium
**Impact:** High
**RTO:** 1 hour
**RPO:** 24 hours

**See:** [Recovery Procedure 1](#procedure-1-database-corruption-recovery)

---

### Scenario 2: Application Failure

**Symptoms:**
- Backend container crashes repeatedly
- HTTP 500 errors
- Services show unhealthy status
- Gunicorn worker timeouts

**Likelihood:** Low
**Impact:** Medium
**RTO:** 30 minutes
**RPO:** 0 hours (no data loss)

**See:** [Recovery Procedure 2](#procedure-2-application-failure-recovery)

---

### Scenario 3: Server Hardware Failure

**Symptoms:**
- Server unresponsive
- Kernel panic
- Hardware errors in logs
- Complete system unavailability

**Likelihood:** Low
**Impact:** Critical
**RTO:** 4 hours
**RPO:** 24 hours

**See:** [Recovery Procedure 3](#procedure-3-server-hardware-failure-recovery)

---

### Scenario 4: Accidental Data Deletion

**Symptoms:**
- Users report missing data
- Audit logs show deletion events
- Table row counts decreased significantly

**Likelihood:** Low
**Impact:** High
**RTO:** 2 hours
**RPO:** 24 hours

**See:** [Recovery Procedure 4](#procedure-4-accidental-data-deletion-recovery)

---

### Scenario 5: Ransomware / Cyber Attack

**Symptoms:**
- Encrypted files
- Ransom note on server
- Unusual network activity
- Unauthorized access in logs

**Likelihood:** Low
**Impact:** Critical
**RTO:** 24-48 hours
**RPO:** 24 hours

**See:** [Recovery Procedure 5](#procedure-5-ransomware-cyber-attack-recovery)

---

### Scenario 6: Complete Datacenter Failure

**Symptoms:**
- Natural disaster (flood, fire, earthquake)
- Power outage (extended, > 24 hours)
- Network infrastructure failure
- Complete site unavailability

**Likelihood:** Very Low
**Impact:** Critical
**RTO:** 8 hours
**RPO:** 24 hours

**See:** [Recovery Procedure 6](#procedure-6-complete-datacenter-failure-recovery)

---

## Recovery Procedures

### Pre-Recovery Checklist

Before starting any recovery:

1. [ ] Notify DR Coordinator
2. [ ] Document current situation (screenshots, logs)
3. [ ] Identify which scenario applies
4. [ ] Verify backups are available
5. [ ] Get approval to proceed (if data will be lost)
6. [ ] Notify users of expected downtime
7. [ ] Start incident log (date, time, actions taken)

---

### Procedure 1: Database Corruption Recovery

**Estimated Time:** 60 minutes

#### Step 1: Assess Damage

```bash
# Try to connect to database
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db

# Check PostgreSQL logs
docker-compose logs postgres | tail -100

# If severe corruption, proceed to restore
```

#### Step 2: Stop Backend Service

```bash
# Prevent new connections to corrupt database
docker-compose stop backend

# Log action
echo "$(date): Stopped backend service - database corruption detected" >> incident.log
```

#### Step 3: Create Emergency Backup

```bash
# Attempt to backup current state (may fail if severely corrupted)
docker-compose exec postgres pg_dump -U vet_clinic_user vet_clinic_db | gzip > emergency_backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Even if it fails, log the attempt
echo "$(date): Emergency backup attempted" >> incident.log
```

#### Step 4: Identify Restore Point

```bash
# List available backups
./scripts/list-backups.sh

# Choose most recent backup before corruption
# Example: backup_vet_clinic_db_20250107_020000.sql.gz
BACKUP_FILE="backup_vet_clinic_db_20250107_020000.sql.gz"

echo "$(date): Selected restore point: $BACKUP_FILE" >> incident.log
```

#### Step 5: Restore Database

```bash
# Execute restore script
./scripts/restore.sh $BACKUP_FILE

# Log action
echo "$(date): Database restore completed from $BACKUP_FILE" >> incident.log
```

#### Step 6: Verify Restoration

```bash
# Check table counts
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT
    table_name,
    (SELECT COUNT(*) FROM users) as users,
    (SELECT COUNT(*) FROM clients) as clients,
    (SELECT COUNT(*) FROM patients) as patients,
    (SELECT COUNT(*) FROM appointments) as appointments;
"

# Compare with production numbers (if known)
# Document discrepancies

echo "$(date): Verification completed - [XX] tables, [YY] users, [ZZ] clients" >> incident.log
```

#### Step 7: Restart Services

```bash
# Restart backend
docker-compose start backend

# Wait for health check
sleep 15

# Verify service status
docker-compose ps

echo "$(date): Services restarted" >> incident.log
```

#### Step 8: Application Validation

```bash
# Test login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test"}'

# Test critical endpoints
curl http://localhost:5000/api/health
curl http://localhost:5000/api/clients
curl http://localhost:5000/api/appointments/today

echo "$(date): Application validation completed" >> incident.log
```

#### Step 9: Notify Users

**Communication Template:**

```
Subject: System Restored - Database Recovery Complete

The Lenox Cat Hospital system has been restored following a database issue.

Downtime: [START TIME] to [END TIME]
Data Loss: Transactions after [BACKUP DATE/TIME] were not recovered
Status: System is now operational

Actions Required:
- Please verify your recent work
- Re-enter any data from [BACKUP DATE/TIME] to [CURRENT TIME]
- Report any discrepancies to IT support

We apologize for the inconvenience.
```

#### Step 10: Post-Recovery Actions

1. [ ] Document root cause of corruption
2. [ ] Update monitoring to detect early
3. [ ] Review backup frequency (consider more frequent backups)
4. [ ] Schedule post-incident review meeting
5. [ ] Update incident log with final notes

---

### Procedure 2: Application Failure Recovery

**Estimated Time:** 30 minutes

#### Step 1: Diagnose Issue

```bash
# Check container status
docker-compose ps

# Check backend logs
docker-compose logs --tail=100 backend

# Common issues:
# - Out of memory
# - Dependency errors
# - Configuration errors
# - Code bugs
```

#### Step 2: Attempt Service Restart

```bash
# Simple restart
docker-compose restart backend

# Wait and check status
sleep 10
docker-compose ps

# If still failing, continue to Step 3
```

#### Step 3: Rebuild Container

```bash
# Stop service
docker-compose stop backend

# Rebuild from source
docker-compose build --no-cache backend

# Start service
docker-compose up -d backend

# Monitor logs
docker-compose logs -f backend
```

#### Step 4: Check Dependencies

```bash
# Verify database connection
docker-compose exec backend python -c "
from app import create_app
app = create_app()
with app.app_context():
    from app import db
    print('Database connected:', db.engine.url)
"

# Verify environment variables
docker-compose exec backend env | grep -E "FLASK|SECRET|DATABASE"
```

#### Step 5: Rollback if Necessary

```bash
# If new deployment caused issue, rollback
git log --oneline -n 5  # Identify previous working version
git checkout <previous-commit-hash>

# Rebuild and redeploy
docker-compose build backend
docker-compose up -d backend
```

#### Step 6: Verify Recovery

```bash
# Test health endpoint
curl http://localhost:5000/api/health

# Test authentication
# Test key endpoints

# Check error logs
docker-compose exec backend cat /app/logs/app.log | tail -20
```

---

### Procedure 3: Server Hardware Failure Recovery

**Estimated Time:** 4 hours

#### Prerequisites

- [ ] New server provisioned (or standby server available)
- [ ] Docker and Docker Compose installed
- [ ] Access to off-site backups
- [ ] Copy of `.env` file (from secure storage)
- [ ] DNS access to update A records

#### Step 1: Provision New Server

```bash
# On new server, install dependencies
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version
docker-compose --version
```

#### Step 2: Clone Application

```bash
# Clone repository
git clone https://github.com/yourusername/LCH.git
cd LCH

# Checkout production branch/tag
git checkout main  # or specific version tag
```

#### Step 3: Restore Configuration

```bash
# Decrypt .env file (if encrypted)
gpg -d /path/to/secure/storage/.env.gpg > .env

# Or manually recreate .env from .env.production template
cp .env.production .env
nano .env  # Enter all required values

# Verify critical variables are set
grep -E "SECRET_KEY|POSTGRES_PASSWORD|DOMAIN_NAME" .env
```

#### Step 4: Retrieve Latest Backup

```bash
# From S3
aws s3 cp s3://lch-backups-offsite/backup_vet_clinic_db_latest.sql.gz ./

# Or from remote server
scp backup-user@backup-server:/backups/lch/backup_latest.sql.gz ./

# Verify backup integrity
gunzip -t backup_vet_clinic_db_latest.sql.gz
```

#### Step 5: Deploy Application

```bash
# Deploy infrastructure
./scripts/deploy.sh production

# Wait for services to start
sleep 30

# Check status
docker-compose ps
```

#### Step 6: Restore Database

```bash
# Copy backup into container volume
docker cp backup_vet_clinic_db_latest.sql.gz lch-postgres:/tmp/

# Restore database
./scripts/restore.sh /tmp/backup_vet_clinic_db_latest.sql.gz

# Verify restoration
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "\dt"
```

#### Step 7: Restore Uploaded Files (if separate backup)

```bash
# If file uploads are backed up separately
docker cp uploads-backup.tar.gz lch-backend:/tmp/
docker-compose exec backend bash -c "cd /app && tar -xzf /tmp/uploads-backup.tar.gz"
```

#### Step 8: Configure SSL

```bash
# If using Let's Encrypt
./scripts/init-ssl.sh

# Or restore SSL certificates from backup
docker cp ssl-certs-backup.tar.gz lch-frontend:/tmp/
docker-compose exec frontend bash -c "tar -xzf /tmp/ssl-certs-backup.tar.gz -C /etc/letsencrypt/"
```

#### Step 9: Update DNS

```bash
# Get new server IP
curl ifconfig.me

# Update DNS A record for your domain
# (Process depends on your DNS provider)
# Point clinic.example.com to [NEW_SERVER_IP]

# Verify DNS propagation
dig +short clinic.example.com
# Should return NEW_SERVER_IP
```

#### Step 10: Verify System

```bash
# Test from external network
curl https://clinic.example.com/api/health

# Test login
# Navigate to https://clinic.example.com
# Log in with admin credentials

# Verify data
# Check that clients, patients, appointments are present
```

#### Step 11: Notify Users

**Communication Template:**

```
Subject: System Restored on New Server

The Lenox Cat Hospital system has been fully restored on a new server following a hardware failure.

New Server Details:
- URL: https://clinic.example.com (unchanged)
- IP Address: [NEW_IP]

Downtime: [START TIME] to [END TIME]
Data Loss: Minimal (last backup was [BACKUP_TIME])

Status: System is fully operational

Please clear your browser cache and cookies, then log in normally.

Report any issues to IT support immediately.
```

---

### Procedure 4: Accidental Data Deletion Recovery

**Estimated Time:** 2 hours

#### Step 1: Confirm Data Loss

```bash
# Identify what was deleted (from user report or audit logs)
docker-compose exec backend grep "delete" /app/logs/audit.log | tail -50

# Check current data state
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT COUNT(*) FROM clients;
SELECT COUNT(*) FROM patients;
SELECT COUNT(*) FROM appointments;
"

# Document findings
echo "$(date): Confirmed deletion - [describe what was deleted]" >> incident.log
```

#### Step 2: Immediate Isolation

```bash
# Stop backend to prevent further changes
docker-compose stop backend

echo "$(date): Backend stopped - preventing further changes" >> incident.log
```

#### Step 3: Create Current State Snapshot

```bash
# Backup current database (including the deletion)
docker-compose exec postgres pg_dump -U vet_clinic_user vet_clinic_db | gzip > current_state_$(date +%Y%m%d_%H%M%S).sql.gz

echo "$(date): Current state snapshot created" >> incident.log
```

#### Step 4: Identify Restore Point

```bash
# Find backup from before the deletion occurred
./scripts/list-backups.sh

# Determine when deletion happened (from audit logs or user report)
# Select backup from before that time

RESTORE_BACKUP="backup_vet_clinic_db_20250107_020000.sql.gz"
echo "$(date): Selected restore point: $RESTORE_BACKUP" >> incident.log
```

#### Step 5: Restore to Test Environment

```bash
# Create temporary test database
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE test_restore;"

# Restore backup to test database
gunzip -c /backups/$RESTORE_BACKUP | docker-compose exec -T postgres psql -U vet_clinic_user -d test_restore

# Verify deleted data is present
docker-compose exec postgres psql -U vet_clinic_user -d test_restore -c "
SELECT * FROM [table_with_deleted_data] WHERE [condition];
"
```

#### Step 6: Export Missing Data

```bash
# Export only the deleted records
docker-compose exec postgres psql -U vet_clinic_user -d test_restore -c "
COPY (SELECT * FROM [table] WHERE [deleted_records_condition])
TO '/tmp/missing_data.csv' WITH CSV HEADER;
"

# Copy out of container
docker cp lch-postgres:/tmp/missing_data.csv ./
```

#### Step 7: Import Missing Data to Production

```bash
# Review CSV file to ensure it's correct
cat missing_data.csv

# Import to production database
docker cp missing_data.csv lch-postgres:/tmp/
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
COPY [table] FROM '/tmp/missing_data.csv' WITH CSV HEADER;
"

echo "$(date): Missing data restored - [XX] records" >> incident.log
```

#### Step 8: Verify Data Integrity

```bash
# Check counts
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT COUNT(*) FROM clients;
SELECT COUNT(*) FROM patients;
"

# Compare with expected counts (from before deletion)
# Verify data relationships are intact

echo "$(date): Data integrity verified" >> incident.log
```

#### Step 9: Cleanup and Restart

```bash
# Remove test database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE test_restore;"

# Restart backend
docker-compose start backend

# Verify services
docker-compose ps

echo "$(date): Services restarted - recovery complete" >> incident.log
```

#### Step 10: Prevent Recurrence

1. [ ] Review permissions (who can delete data?)
2. [ ] Implement soft deletes (status='deleted' instead of actual DELETE)
3. [ ] Add confirmation prompts for bulk deletions
4. [ ] Increase backup frequency if needed
5. [ ] Train staff on data deletion procedures

---

### Procedure 5: Ransomware / Cyber Attack Recovery

**⚠️ CRITICAL:** This is a security incident. Follow incident response procedures.

**Estimated Time:** 24-48 hours

#### Step 1: Immediate Isolation

```bash
# IMMEDIATELY disconnect server from network
sudo iptables -I INPUT -j DROP
sudo iptables -I OUTPUT -j DROP

# Or physically disconnect network cable

# DO NOT shut down the server yet (preserve evidence)

echo "$(date): Server isolated from network - ransomware detected" >> incident.log
```

#### Step 2: Notify Security Team

- [ ] Contact security officer
- [ ] Contact law enforcement (if required by policy)
- [ ] Contact cyber insurance provider
- [ ] Preserve all logs and evidence
- [ ] DO NOT pay ransom

#### Step 3: Assess Damage

```bash
# Check which files are encrypted
find /var/lib/docker/volumes -type f -name "*.encrypted" -o -name "*.locked"

# Check for ransom notes
find / -type f -name "*RANSOM*" -o -name "*README*"

# Document findings
ls -lR /var/lib/docker/volumes > file_list_$(date +%Y%m%d_%H%M%S).txt
```

#### Step 4: Preserve Evidence

```bash
# Create forensic image (if required)
dd if=/dev/sda of=/mnt/external/forensic_image.dd bs=4M

# Save logs
docker-compose logs > docker_logs_$(date +%Y%m%d_%H%M%S).txt
sudo journalctl > system_logs_$(date +%Y%m%d_%H%M%S).txt
sudo cat /var/log/auth.log > auth_logs_$(date +%Y%m%d_%H%M%S).txt

# Copy to secure location (external drive, not network)
```

#### Step 5: Provision Clean Server

```bash
# DO NOT restore to infected server
# Provision completely new server from scratch

# Follow "Server Hardware Failure Recovery" procedure
# Use backups from BEFORE the attack
```

#### Step 6: Verify Backup Integrity

```bash
# Ensure backups are not encrypted
gunzip -t backup_file.sql.gz

# Check backup dates (use backup from before attack)
./scripts/list-backups.sh

# Scan backups for malware (if possible)
clamscan backup_file.sql.gz
```

#### Step 7: Restore on Clean Server

Follow Procedure 3 (Server Hardware Failure Recovery) to restore on new server.

#### Step 8: Security Hardening

Before making system available:

1. [ ] Change ALL passwords (database, admin users, SSH)
2. [ ] Rotate SECRET_KEY
3. [ ] Update all software packages
4. [ ] Review firewall rules
5. [ ] Enable two-factor authentication (if available)
6. [ ] Review and remove any unauthorized users
7. [ ] Scan for backdoors and malware
8. [ ] Enable intrusion detection
9. [ ] Review audit logs for attack vector

#### Step 9: Gradual Restoration

```bash
# DO NOT restore everything at once
# Restore in phases, verifying each step

# Phase 1: Database only
# Phase 2: Application
# Phase 3: User access (limited users first)
# Phase 4: Full production
```

#### Step 10: Post-Incident Actions

1. [ ] Complete incident report
2. [ ] Identify attack vector
3. [ ] Implement additional security controls
4. [ ] Train staff on security awareness
5. [ ] Review and update security policies
6. [ ] Consider penetration testing
7. [ ] Review cyber insurance coverage

---

### Procedure 6: Complete Datacenter Failure Recovery

**Estimated Time:** 8 hours

**Prerequisites:**
- [ ] Alternate datacenter or cloud provider account
- [ ] Off-site backups accessible
- [ ] DNS access
- [ ] Secure copy of `.env` configuration

#### Step 1: Activate Disaster Recovery Site

```bash
# Provision new infrastructure
# Options:
# 1. Pre-configured DR site (fastest)
# 2. Cloud provider (AWS, Azure, GCP, DigitalOcean)
# 3. Backup datacenter

# Document new infrastructure details
echo "$(date): DR site activation - [provider/location]" >> incident.log
```

#### Step 2: Install Dependencies

```bash
# On new server/instance
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git

sudo systemctl start docker
sudo systemctl enable docker

# Verify
docker --version
docker-compose --version
```

#### Step 3: Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/LCH.git
cd LCH

# Restore .env configuration
# (from secure off-site storage)

# Deploy
./scripts/deploy.sh production
```

#### Step 4: Restore Data

```bash
# Retrieve backups from off-site location
# From S3:
aws s3 cp s3://lch-backups-offsite/backup_latest.sql.gz ./

# From backup datacenter:
scp backup-user@backup-site:/backups/lch/backup_latest.sql.gz ./

# Restore database
./scripts/restore.sh backup_latest.sql.gz

# Restore uploaded files
aws s3 sync s3://lch-files-backup/ ./uploads/
docker cp uploads/ lch-backend:/app/uploads/
```

#### Step 5: Configure Networking

```bash
# Get new server IP
NEW_IP=$(curl -s ifconfig.me)

# Update DNS records
# Point clinic.example.com to $NEW_IP

# Update firewall rules
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

echo "$(date): DNS updated to $NEW_IP" >> incident.log
```

#### Step 6: Initialize SSL

```bash
# Wait for DNS propagation
while ! dig +short clinic.example.com | grep -q $NEW_IP; do
    echo "Waiting for DNS propagation..."
    sleep 60
done

# Initialize SSL certificates
./scripts/init-ssl.sh
```

#### Step 7: Comprehensive Testing

```bash
# Test from external network
curl https://clinic.example.com/api/health

# Test all critical functions:
# - User login
# - View clients
# - View patients
# - Schedule appointment
# - Create invoice
# - Process payment

# Document test results
echo "$(date): System testing completed - all critical functions operational" >> incident.log
```

#### Step 8: Gradual User Enablement

```bash
# Phase 1: Enable access for administrators only
# - Test thoroughly
# - Verify data integrity

# Phase 2: Enable access for select staff
# - Monitor for issues
# - Gather feedback

# Phase 3: Enable full access
# - Announce to all users
# - Monitor system performance
```

#### Step 9: Monitor Closely

```bash
# Set up real-time monitoring
docker stats

# Watch logs
docker-compose logs -f

# Monitor resource usage
htop

# Check for errors
watch -n 5 'docker-compose exec backend cat /app/logs/app.log | tail -20'
```

#### Step 10: Plan Original Site Recovery

When original site is restored:

1. [ ] Decide: Failback or stay at DR site?
2. [ ] If failback:
   - Create backup of DR site
   - Restore original infrastructure
   - Migrate data back
   - Update DNS
   - Verify
3. [ ] If staying at DR:
   - Update documentation
   - Reconfigure monitoring
   - Update contracts/billing

---

## Testing & Validation

### Disaster Recovery Test Schedule

| Test Type | Frequency | Next Test Date |
|-----------|-----------|----------------|
| Backup restoration test | Monthly | [Date] |
| Application failure simulation | Quarterly | [Date] |
| Full DR drill | Annually | [Date] |
| Tabletop exercise | Semi-annually | [Date] |

### Monthly Backup Restoration Test

**Procedure:**

```bash
# 1. Create test environment
export COMPOSE_PROJECT_NAME=dr-test
docker-compose up -d

# 2. Restore latest backup
LATEST_BACKUP=$(ls -t /backups/*.sql.gz | head -1)
./scripts/restore.sh $LATEST_BACKUP

# 3. Verify data
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "
SELECT
    'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'clients', COUNT(*) FROM clients
UNION ALL
SELECT 'patients', COUNT(*) FROM patients;
"

# 4. Test application
curl http://localhost:5000/api/health

# 5. Document results
echo "Monthly DR test - $(date)" >> dr-test-log.txt
echo "Backup: $LATEST_BACKUP" >> dr-test-log.txt
echo "Result: [PASS/FAIL]" >> dr-test-log.txt

# 6. Cleanup
docker-compose -p dr-test down -v
```

### Quarterly Full DR Drill

**Procedure:**

1. **Preparation (1 week before)**
   - [ ] Schedule maintenance window
   - [ ] Notify users
   - [ ] Prepare DR team
   - [ ] Review procedures

2. **Execution (During drill)**
   - [ ] Simulate disaster (choose scenario)
   - [ ] Activate DR plan
   - [ ] Execute recovery procedures
   - [ ] Document all steps
   - [ ] Time each phase

3. **Validation**
   - [ ] Verify all services operational
   - [ ] Test all critical functions
   - [ ] Verify data integrity
   - [ ] Measure RTO/RPO achieved

4. **Debrief (Within 1 week)**
   - [ ] Review what went well
   - [ ] Identify issues
   - [ ] Update procedures
   - [ ] Assign action items
   - [ ] Update DR plan

### Test Results Documentation

Create a test log for each DR test:

```
DR Test Log
===========
Date: [YYYY-MM-DD]
Test Type: [Monthly Backup Restoration / Quarterly DR Drill / etc.]
Scenario: [What was tested]
Team Members: [Who participated]

Timeline:
- [HH:MM] - [Action taken]
- [HH:MM] - [Action taken]
...

RTO Achieved: [X hours] (Target: Y hours)
RPO Achieved: [X hours] (Target: Y hours)

Results:
✓ [What worked well]
✗ [What failed]

Issues Identified:
1. [Issue description]
2. [Issue description]

Action Items:
1. [Action] - Assigned to: [Name] - Due: [Date]
2. [Action] - Assigned to: [Name] - Due: [Date]

Next Test: [Date]
```

---

## Contact Information

### Disaster Recovery Team

| Name | Role | Phone | Email | Alternate Contact |
|------|------|-------|-------|-------------------|
| [Name] | DR Coordinator | [Phone] | [Email] | [Alternate] |
| [Name] | System Admin | [Phone] | [Email] | [Alternate] |
| [Name] | DB Admin | [Phone] | [Email] | [Alternate] |
| [Name] | Security Officer | [Phone] | [Email] | [Alternate] |

### Vendors & Service Providers

| Service | Provider | Account # | Contact | Support Phone | Support Email |
|---------|----------|-----------|---------|---------------|---------------|
| Hosting | [Provider] | [Account] | [Name] | [Phone] | [Email] |
| Domain/DNS | [Provider] | [Account] | [Name] | [Phone] | [Email] |
| Backup Storage | [Provider] | [Account] | [Name] | [Phone] | [Email] |
| Cloud Provider | [Provider] | [Account] | [Name] | [Phone] | [Email] |
| Cyber Insurance | [Provider] | [Policy #] | [Agent] | [Phone] | [Email] |

### Emergency Escalation

1. **System Administrator** - [Name] - [Phone]
2. **IT Manager** - [Name] - [Phone]
3. **Operations Director** - [Name] - [Phone]
4. **Executive Team** - [Name] - [Phone]

### External Resources

- **Docker Support:** https://docs.docker.com/support/
- **PostgreSQL Support:** https://www.postgresql.org/support/
- **SSL Certificate Issues:** https://letsencrypt.org/docs/
- **Security Incident:** [Your security incident response provider]

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-07 | [Your Name] | Initial document creation |
| | | | |
| | | | |

### Review Log

| Date | Reviewer | Approved | Notes |
|------|----------|----------|-------|
| | | [ ] | |
| | | [ ] | |

### Test Log

| Date | Test Type | Result | Next Test Due |
|------|-----------|--------|---------------|
| | | | |
| | | | |

---

**Document Classification:** CONFIDENTIAL
**Distribution:** Disaster Recovery Team Only
**Storage Location:** Secure off-site location + encrypted cloud storage
**Review Schedule:** Quarterly
**Next Review Date:** [3 months from creation]

---

## Appendix A: Recovery Checklists

### Quick Reference Checklist

**For any disaster:**

1. [ ] Notify DR Coordinator
2. [ ] Assess situation
3. [ ] Identify scenario
4. [ ] Document current state
5. [ ] Review appropriate procedure
6. [ ] Execute recovery steps
7. [ ] Verify restoration
8. [ ] Notify users
9. [ ] Conduct post-incident review
10. [ ] Update documentation

### Pre-Disaster Checklist

**Verify monthly:**

- [ ] Backups running successfully
- [ ] Off-site replication working
- [ ] `.env` file backed up securely
- [ ] DR team contact info current
- [ ] Service provider accounts accessible
- [ ] DNS credentials accessible
- [ ] Documentation up to date

---

**END OF DISASTER RECOVERY PLAN**

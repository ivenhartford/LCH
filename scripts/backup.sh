#!/bin/bash
# Database Backup Script for Lenox Cat Hospital
# Performs automated PostgreSQL database backups with rotation

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration (can be overridden by environment variables)
BACKUP_DIR="${BACKUP_DIR:-/backups}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-vet_clinic_db}"
POSTGRES_USER="${POSTGRES_USER:-vet_clinic_user}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"

# Timestamp for backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="backup_${POSTGRES_DB}_${TIMESTAMP}.sql"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE_GZ}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Lenox Cat Hospital - Database Backup${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Backup started at: $(date)"
echo "Database: ${POSTGRES_DB}"
echo "Host: ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo "Backup directory: ${BACKUP_DIR}"
echo "Retention: ${BACKUP_RETENTION_DAYS} days"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Check if PostgreSQL is accessible
echo -e "${YELLOW}Checking database connectivity...${NC}"
if ! pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > /dev/null 2>&1; then
    echo -e "${RED}✗ Database is not accessible${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database is accessible${NC}"

# Perform database backup
echo -e "${YELLOW}Creating database backup...${NC}"
if PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --format=plain \
    --verbose \
    --no-owner \
    --no-acl \
    2>&1 | gzip -${COMPRESSION_LEVEL} > "${BACKUP_PATH}"; then

    # Get backup file size
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    echo -e "${GREEN}✓ Backup created successfully${NC}"
    echo "  File: ${BACKUP_FILE_GZ}"
    echo "  Size: ${BACKUP_SIZE}"
else
    echo -e "${RED}✗ Backup failed${NC}"
    rm -f "${BACKUP_PATH}"
    exit 1
fi

# Verify backup integrity
echo -e "${YELLOW}Verifying backup integrity...${NC}"
if gunzip -t "${BACKUP_PATH}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backup file is valid${NC}"
else
    echo -e "${RED}✗ Backup file is corrupted${NC}"
    exit 1
fi

# Create metadata file
METADATA_FILE="${BACKUP_DIR}/backup_${POSTGRES_DB}_${TIMESTAMP}.meta"
cat > "${METADATA_FILE}" <<EOF
{
  "database": "${POSTGRES_DB}",
  "host": "${POSTGRES_HOST}",
  "timestamp": "${TIMESTAMP}",
  "date": "$(date -u +"%Y-%m-%d %H:%M:%S UTC")",
  "backup_file": "${BACKUP_FILE_GZ}",
  "backup_size": "${BACKUP_SIZE}",
  "postgres_version": "$(PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c 'SELECT version();' | xargs)"
}
EOF

# Rotate old backups (delete backups older than retention period)
echo -e "${YELLOW}Rotating old backups...${NC}"
DELETED_COUNT=0
while IFS= read -r -d '' old_backup; do
    rm -f "$old_backup"
    # Also remove corresponding metadata file
    META_FILE="${old_backup%.sql.gz}.meta"
    rm -f "$META_FILE"
    ((DELETED_COUNT++))
done < <(find "${BACKUP_DIR}" -name "backup_${POSTGRES_DB}_*.sql.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} -print0)

if [ ${DELETED_COUNT} -gt 0 ]; then
    echo -e "${GREEN}✓ Deleted ${DELETED_COUNT} old backup(s)${NC}"
else
    echo "No old backups to delete"
fi

# Count total backups
TOTAL_BACKUPS=$(find "${BACKUP_DIR}" -name "backup_${POSTGRES_DB}_*.sql.gz" -type f | wc -l)
echo "Total backups: ${TOTAL_BACKUPS}"

# Backup summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Backup completed successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Backup file: ${BACKUP_PATH}"
echo "Metadata file: ${METADATA_FILE}"
echo "Completed at: $(date)"

# Return success
exit 0

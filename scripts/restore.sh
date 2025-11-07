#!/bin/bash
# Database Restore Script for Lenox Cat Hospital
# Restores PostgreSQL database from a backup file

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration (can be overridden by environment variables)
BACKUP_DIR="${BACKUP_DIR:-/backups}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-vet_clinic_db}"
POSTGRES_USER="${POSTGRES_USER:-vet_clinic_user}"

# Parse command line arguments
BACKUP_FILE="$1"

# Function to display usage
usage() {
    echo "Usage: $0 <backup-file>"
    echo ""
    echo "Examples:"
    echo "  $0 backup_vet_clinic_db_20250107_140000.sql.gz"
    echo "  $0 /backups/backup_vet_clinic_db_20250107_140000.sql.gz"
    echo ""
    echo "Available backups:"
    find "${BACKUP_DIR}" -name "backup_*.sql.gz" -type f -printf "  %f (size: %s bytes, modified: %TY-%Tm-%Td %TH:%TM)\n" | sort -r | head -10
    exit 1
}

# Check if backup file argument is provided
if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not specified${NC}"
    usage
fi

# If backup file is just a filename, prepend backup directory
if [[ "$BACKUP_FILE" != /* ]]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: ${BACKUP_FILE}${NC}"
    usage
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Lenox Cat Hospital - Database Restore${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Restore started at: $(date)"
echo "Database: ${POSTGRES_DB}"
echo "Host: ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo "Backup file: ${BACKUP_FILE}"

# Show metadata if available
METADATA_FILE="${BACKUP_FILE%.sql.gz}.meta"
if [ -f "$METADATA_FILE" ]; then
    echo -e "${BLUE}Backup metadata:${NC}"
    cat "$METADATA_FILE"
fi

# Warning prompt
echo ""
echo -e "${YELLOW}⚠ WARNING: This will REPLACE the current database!${NC}"
echo -e "${YELLOW}⚠ All existing data in '${POSTGRES_DB}' will be LOST!${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Restore cancelled by user${NC}"
    exit 0
fi

# Check if PostgreSQL is accessible
echo -e "${YELLOW}Checking database connectivity...${NC}"
if ! pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > /dev/null 2>&1; then
    echo -e "${RED}✗ Database is not accessible${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database is accessible${NC}"

# Verify backup file integrity
echo -e "${YELLOW}Verifying backup file integrity...${NC}"
if ! gunzip -t "${BACKUP_FILE}" > /dev/null 2>&1; then
    echo -e "${RED}✗ Backup file is corrupted${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backup file is valid${NC}"

# Create a pre-restore backup
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PRE_RESTORE_BACKUP="${BACKUP_DIR}/pre_restore_${POSTGRES_DB}_${TIMESTAMP}.sql.gz"
echo -e "${YELLOW}Creating pre-restore backup...${NC}"
if PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --format=plain \
    --no-owner \
    --no-acl \
    2>/dev/null | gzip -6 > "${PRE_RESTORE_BACKUP}"; then
    echo -e "${GREEN}✓ Pre-restore backup created: ${PRE_RESTORE_BACKUP}${NC}"
else
    echo -e "${YELLOW}Warning: Pre-restore backup failed (continuing anyway)${NC}"
fi

# Terminate existing connections to the database
echo -e "${YELLOW}Terminating existing database connections...${NC}"
PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1 || true
echo -e "${GREEN}✓ Connections terminated${NC}"

# Drop and recreate the database
echo -e "${YELLOW}Recreating database...${NC}"
PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d postgres \
    <<EOF
DROP DATABASE IF EXISTS ${POSTGRES_DB};
CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};
EOF
echo -e "${GREEN}✓ Database recreated${NC}"

# Restore the backup
echo -e "${YELLOW}Restoring database from backup...${NC}"
if gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --single-transaction \
    > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database restored successfully${NC}"
else
    echo -e "${RED}✗ Database restore failed${NC}"
    echo -e "${YELLOW}Attempting to restore from pre-restore backup...${NC}"
    if [ -f "${PRE_RESTORE_BACKUP}" ]; then
        gunzip -c "${PRE_RESTORE_BACKUP}" | PGPASSWORD="${POSTGRES_PASSWORD}" psql \
            -h "${POSTGRES_HOST}" \
            -p "${POSTGRES_PORT}" \
            -U "${POSTGRES_USER}" \
            -d "${POSTGRES_DB}" \
            > /dev/null 2>&1 || true
        echo -e "${YELLOW}Check database status manually${NC}"
    fi
    exit 1
fi

# Verify restoration
echo -e "${YELLOW}Verifying restoration...${NC}"
TABLE_COUNT=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

echo -e "${GREEN}✓ Restoration verified (${TABLE_COUNT} tables)${NC}"

# Restore summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Restore completed successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Backup file: ${BACKUP_FILE}"
echo "Tables restored: ${TABLE_COUNT}"
echo "Pre-restore backup: ${PRE_RESTORE_BACKUP}"
echo "Completed at: $(date)"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Restart the backend service to clear any cached data"
echo "  2. Verify application functionality"
echo "  3. Check logs for any issues"

# Return success
exit 0

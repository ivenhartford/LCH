#!/bin/bash
# List and Manage Database Backups for Lenox Cat Hospital

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
POSTGRES_DB="${POSTGRES_DB:-vet_clinic_db}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Lenox Cat Hospital - Backup Management${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Backup directory: ${BACKUP_DIR}"
echo "Database: ${POSTGRES_DB}"
echo ""

# Check if backup directory exists
if [ ! -d "${BACKUP_DIR}" ]; then
    echo -e "${YELLOW}No backup directory found${NC}"
    exit 0
fi

# Count backups
BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "backup_${POSTGRES_DB}_*.sql.gz" -type f 2>/dev/null | wc -l)

if [ ${BACKUP_COUNT} -eq 0 ]; then
    echo -e "${YELLOW}No backups found${NC}"
    exit 0
fi

echo -e "${GREEN}Found ${BACKUP_COUNT} backup(s)${NC}"
echo ""

# List backups with details
echo -e "${BLUE}Available backups:${NC}"
echo "--------------------------------------------------------------------------------"
printf "%-40s %-12s %-20s\n" "Filename" "Size" "Modified"
echo "--------------------------------------------------------------------------------"

find "${BACKUP_DIR}" -name "backup_${POSTGRES_DB}_*.sql.gz" -type f -printf "%f\t%s\t%TY-%Tm-%Td %TH:%TM:%TS\n" 2>/dev/null | \
    sort -r | \
    while IFS=$'\t' read -r filename size modified; do
        # Convert size to human readable format
        if [ $size -lt 1024 ]; then
            size_human="${size}B"
        elif [ $size -lt 1048576 ]; then
            size_human="$((size / 1024))KB"
        elif [ $size -lt 1073741824 ]; then
            size_human="$((size / 1048576))MB"
        else
            size_human="$((size / 1073741824))GB"
        fi
        printf "%-40s %-12s %-20s\n" "$filename" "$size_human" "$modified"
    done

echo "--------------------------------------------------------------------------------"

# Calculate total backup size
TOTAL_SIZE=$(find "${BACKUP_DIR}" -name "backup_${POSTGRES_DB}_*.sql.gz" -type f -printf "%s\n" 2>/dev/null | awk '{sum+=$1} END {print sum}')

if [ -z "$TOTAL_SIZE" ] || [ "$TOTAL_SIZE" -eq 0 ]; then
    TOTAL_SIZE_HUMAN="0B"
elif [ $TOTAL_SIZE -lt 1024 ]; then
    TOTAL_SIZE_HUMAN="${TOTAL_SIZE}B"
elif [ $TOTAL_SIZE -lt 1048576 ]; then
    TOTAL_SIZE_HUMAN="$((TOTAL_SIZE / 1024))KB"
elif [ $TOTAL_SIZE -lt 1073741824 ]; then
    TOTAL_SIZE_HUMAN="$((TOTAL_SIZE / 1048576))MB"
else
    TOTAL_SIZE_HUMAN="$((TOTAL_SIZE / 1073741824))GB"
fi

echo ""
echo -e "${GREEN}Total backup size: ${TOTAL_SIZE_HUMAN}${NC}"

# Show oldest and newest backups
OLDEST=$(find "${BACKUP_DIR}" -name "backup_${POSTGRES_DB}_*.sql.gz" -type f -printf "%f\n" 2>/dev/null | sort | head -1)
NEWEST=$(find "${BACKUP_DIR}" -name "backup_${POSTGRES_DB}_*.sql.gz" -type f -printf "%f\n" 2>/dev/null | sort | tail -1)

echo ""
echo -e "${BLUE}Oldest backup: ${OLDEST}${NC}"
echo -e "${BLUE}Newest backup: ${NEWEST}${NC}"

# Show disk usage
echo ""
echo -e "${BLUE}Disk usage:${NC}"
df -h "${BACKUP_DIR}" | tail -1 | awk '{print "  Used: "$3" / "$2" ("$5" full)"}'

echo ""

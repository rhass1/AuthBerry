#!/bin/bash

# AuthBerry Database Backup Script
# Handles TPM-encrypted secrets properly

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS=7
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="auth_berry_backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="${BACKUP_FILE}.gz"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "Starting database backup..."

# Check if containers are running
if ! docker ps --format "table {{.Names}}" | grep -q "auth_berry_mariadb"; then
    log "ERROR: MariaDB container is not running"
    exit 1
fi

if ! docker ps --format "table {{.Names}}" | grep -q "auth_berry_flask"; then
    log "ERROR: Flask container is not running"
    exit 1
fi

log "Containers are running, proceeding with backup..."

# Get database credentials using TPM unsealing
log "Retrieving database credentials from TPM..."
DB_PASSWORD=$(docker exec auth_berry_mariadb python3 -c "
import sys
sys.path.append('/usr/local/bin')
from tpm_manager import TPMManager
tpm = TPMManager(secrets_dir='/secrets')
tpm.generate_or_load_primary_key()
print(tpm.unseal_secret('mariadb_user').decode('utf-8').strip())
")

DB_ROOT_PASSWORD=$(docker exec auth_berry_mariadb python3 -c "
import sys
sys.path.append('/usr/local/bin')
from tpm_manager import TPMManager
tpm = TPMManager(secrets_dir='/secrets')
tpm.generate_or_load_primary_key()
print(tpm.unseal_secret('mariadb_root').decode('utf-8').strip())
")

if [ -z "$DB_PASSWORD" ] || [ -z "$DB_ROOT_PASSWORD" ]; then
    log "ERROR: Failed to retrieve database credentials from TPM"
    exit 1
fi

log "Retrieved database credentials from TPM successfully"

# Perform backup
log "Creating database backup..."
if docker exec auth_berry_mariadb mariadb-dump \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --add-drop-database \
    --databases auth_berry \
    -u root \
    -p"$DB_ROOT_PASSWORD" > "${BACKUP_DIR}/${BACKUP_FILE}"; then
    
    log "Database dump completed successfully"
    
    # Compress the backup
    log "Compressing backup file..."
    gzip "${BACKUP_DIR}/${BACKUP_FILE}"
    
    # Set secure permissions
    chmod 600 "${BACKUP_DIR}/${COMPRESSED_FILE}"
    
    log "Backup created: ${BACKUP_DIR}/${COMPRESSED_FILE}"
    
    # Get file size
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${COMPRESSED_FILE}" | cut -f1)
    log "Backup size: $BACKUP_SIZE"
    
else
    log "ERROR: Database backup failed"
    exit 1
fi

# Cleanup old backups
log "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "auth_berry_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
REMAINING_BACKUPS=$(find "$BACKUP_DIR" -name "auth_berry_backup_*.sql.gz" -type f | wc -l)
log "Cleanup completed. $REMAINING_BACKUPS backup(s) remaining."

log "Backup process completed successfully"

# Optional: Send backup to external location
if [ -n "${BACKUP_REMOTE_PATH}" ]; then
    log "Copying backup to remote location: ${BACKUP_REMOTE_PATH}"
    rsync -av "${BACKUP_DIR}/${COMPRESSED_FILE}" "${BACKUP_REMOTE_PATH}/" || log "WARNING: Remote backup copy failed"
fi

log "AuthBerry database backup finished" 
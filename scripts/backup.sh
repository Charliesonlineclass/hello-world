#!/bin/bash
# =============================================================================
# SCORPION KING - Backup Script
# =============================================================================
# Backs up ChromaDB data, configurations, and important files.
#
# USAGE:
#   ./scripts/backup.sh              # Create timestamped backup
#   ./scripts/backup.sh --push       # Backup and push to GitHub
#   ./scripts/backup.sh --restore <file>  # Restore from backup
#
# =============================================================================

set -e

# Configuration
SCORPION_DIR="${SCORPION_DIR:-$(dirname "$(dirname "$(readlink -f "$0")")")}"
BACKUP_DIR="${SCORPION_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="scorpion_backup_${TIMESTAMP}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Options
PUSH_TO_GITHUB=false
RESTORE_FILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push) PUSH_TO_GITHUB=true; shift ;;
        --restore) RESTORE_FILE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# =============================================================================
# RESTORE FUNCTION
# =============================================================================

restore_backup() {
    if [ ! -f "$RESTORE_FILE" ]; then
        log_error "Backup file not found: $RESTORE_FILE"
        exit 1
    fi

    log_info "Restoring from: $RESTORE_FILE"
    log_warning "This will overwrite current data. Continue? (y/N)"
    read -r confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi

    # Stop services
    log_info "Stopping services..."
    cd "${SCORPION_DIR}/body/docker" && docker-compose down 2>/dev/null || true

    # Extract backup
    log_info "Extracting backup..."
    cd "${SCORPION_DIR}"
    tar -xzf "$RESTORE_FILE"

    # Restart services
    log_info "Restarting services..."
    cd "${SCORPION_DIR}/body/docker" && docker-compose up -d 2>/dev/null || true

    log_success "Restore complete!"
    exit 0
}

# Check for restore mode
if [ -n "$RESTORE_FILE" ]; then
    restore_backup
fi

# =============================================================================
# BACKUP FUNCTION
# =============================================================================

create_backup() {
    echo -e "${BLUE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                 SCORPION BACKUP SCRIPT                        ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    log_info "Starting backup: ${BACKUP_NAME}"
    log_info "Source: ${SCORPION_DIR}"

    # Create backup directory
    mkdir -p "${BACKUP_DIR}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    mkdir -p "${BACKUP_PATH}"

    # =================
    # BACKUP CHROMADB
    # =================
    log_info "Backing up ChromaDB data..."
    if [ -d "${SCORPION_DIR}/chromadb_data" ]; then
        cp -r "${SCORPION_DIR}/chromadb_data" "${BACKUP_PATH}/"
        log_success "ChromaDB data backed up"
    elif [ -d "${SCORPION_DIR}/body/docker/chromadb_data" ]; then
        cp -r "${SCORPION_DIR}/body/docker/chromadb_data" "${BACKUP_PATH}/"
        log_success "ChromaDB data backed up"
    else
        log_warning "ChromaDB data not found"
    fi

    # =================
    # BACKUP CONFIGS
    # =================
    log_info "Backing up configurations..."
    mkdir -p "${BACKUP_PATH}/config"

    # Docker env
    if [ -f "${SCORPION_DIR}/body/docker/.env" ]; then
        cp "${SCORPION_DIR}/body/docker/.env" "${BACKUP_PATH}/config/"
        log_success "Docker .env backed up"
    fi

    # Agenda
    if [ -f "${SCORPION_DIR}/daemon/agenda.json" ]; then
        cp "${SCORPION_DIR}/daemon/agenda.json" "${BACKUP_PATH}/config/"
        log_success "Agenda backed up"
    fi

    # =================
    # BACKUP DATA
    # =================
    log_info "Backing up application data..."
    mkdir -p "${BACKUP_PATH}/data"

    # Leads
    if [ -d "${SCORPION_DIR}/leads" ]; then
        cp -r "${SCORPION_DIR}/leads" "${BACKUP_PATH}/data/"
        log_success "Leads data backed up"
    fi

    # Pipeline
    if [ -d "${SCORPION_DIR}/pipeline" ]; then
        cp -r "${SCORPION_DIR}/pipeline" "${BACKUP_PATH}/data/"
        log_success "Pipeline data backed up"
    fi

    # Call logs
    if [ -d "${SCORPION_DIR}/call_logs" ]; then
        cp -r "${SCORPION_DIR}/call_logs" "${BACKUP_PATH}/data/"
        log_success "Call logs backed up"
    fi

    # Appointments
    if [ -d "${SCORPION_DIR}/appointments" ]; then
        cp -r "${SCORPION_DIR}/appointments" "${BACKUP_PATH}/data/"
        log_success "Appointments backed up"
    fi

    # Quotes
    if [ -d "${SCORPION_DIR}/quotes" ]; then
        cp -r "${SCORPION_DIR}/quotes" "${BACKUP_PATH}/data/"
        log_success "Quotes backed up"
    fi

    # Transcripts
    if [ -d "${SCORPION_DIR}/transcripts" ]; then
        cp -r "${SCORPION_DIR}/transcripts" "${BACKUP_PATH}/data/"
        log_success "Transcripts backed up"
    fi

    # =================
    # BACKUP SECURITY
    # =================
    log_info "Backing up security data..."
    if [ -d "${SCORPION_DIR}/security" ]; then
        cp -r "${SCORPION_DIR}/security" "${BACKUP_PATH}/"
        log_success "Security data backed up"
    fi

    # =================
    # CREATE ARCHIVE
    # =================
    log_info "Creating compressed archive..."
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
    rm -rf "${BACKUP_NAME}"

    ARCHIVE_PATH="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)

    log_success "Backup created: ${ARCHIVE_PATH}"
    log_info "Archive size: ${ARCHIVE_SIZE}"

    # =================
    # CLEANUP OLD BACKUPS
    # =================
    log_info "Cleaning up old backups (keeping last 7)..."
    cd "${BACKUP_DIR}"
    ls -t scorpion_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm --
    log_success "Cleanup complete"

    # =================
    # PUSH TO GITHUB
    # =================
    if $PUSH_TO_GITHUB; then
        log_info "Pushing to GitHub..."
        cd "${SCORPION_DIR}"

        git add -A
        git commit -m "Backup: ${TIMESTAMP}" 2>/dev/null || log_warning "Nothing to commit"
        git push 2>/dev/null || log_warning "Push failed (check remote config)"

        log_success "Pushed to GitHub"
    fi

    # =================
    # SUMMARY
    # =================
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   BACKUP COMPLETE                             ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Archive: ${ARCHIVE_PATH}"
    echo "  Size: ${ARCHIVE_SIZE}"
    echo "  Timestamp: ${TIMESTAMP}"
    echo ""
    echo "  To restore: ./scripts/backup.sh --restore ${ARCHIVE_PATH}"
    echo ""
}

# =============================================================================
# MAIN
# =============================================================================

create_backup

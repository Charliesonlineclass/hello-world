#!/bin/bash
#
# SCORPION_BRAIN GitHub Sync Script
# ==================================
# Pulls latest SCORPION_BRAIN code from GitHub
# Run this on your Linux machine to sync
#

set -e

# Configuration
REPO_URL="${SCORPION_REPO_URL:-https://github.com/YOUR_USERNAME/hello-world.git}"
BRANCH="${SCORPION_BRANCH:-main}"
TARGET_DIR="${SCORPION_DIR:-$HOME/SCORPION_BRAIN}"
BACKUP_DIR="$HOME/.scorpion_backup"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🦂 SCORPION_BRAIN Sync Script${NC}"
echo "=================================="
echo ""

# Function to print status
status() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    error "Git is not installed. Please install git first."
fi

# Check if target directory exists
if [ -d "$TARGET_DIR" ]; then
    if [ -d "$TARGET_DIR/.git" ]; then
        # It's a git repo, pull latest
        echo "Existing SCORPION_BRAIN found. Pulling latest..."

        cd "$TARGET_DIR"

        # Stash any local changes
        if [ -n "$(git status --porcelain)" ]; then
            warning "Local changes detected, stashing..."
            git stash
        fi

        # Pull latest
        git fetch origin "$BRANCH"
        git checkout "$BRANCH"
        git pull origin "$BRANCH"

        status "Pulled latest from $BRANCH"

    else
        # Not a git repo, backup and clone fresh
        warning "Directory exists but is not a git repo"

        echo "Backing up existing files..."
        BACKUP_NAME="scorpion_backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        mv "$TARGET_DIR" "$BACKUP_DIR/$BACKUP_NAME"
        status "Backup created: $BACKUP_DIR/$BACKUP_NAME"

        echo "Cloning fresh..."
        git clone -b "$BRANCH" "$REPO_URL" "$TARGET_DIR"
        status "Cloned from $REPO_URL"
    fi
else
    # Fresh clone
    echo "No existing SCORPION_BRAIN found. Cloning..."

    # Create parent directory if needed
    mkdir -p "$(dirname "$TARGET_DIR")"

    git clone -b "$BRANCH" "$REPO_URL" "$TARGET_DIR"
    status "Cloned from $REPO_URL"
fi

# Navigate to directory
cd "$TARGET_DIR"

# Show what we have
echo ""
echo -e "${BLUE}📁 SCORPION_BRAIN Structure:${NC}"
echo "----------------------------"

if [ -d "SCORPION_BRAIN" ]; then
    # If cloned repo has SCORPION_BRAIN subdirectory
    find SCORPION_BRAIN -type f -name "*.py" | head -20
else
    # If we're directly in SCORPION_BRAIN
    find . -type f -name "*.py" -not -path "./.git/*" | head -20
fi

echo ""

# Count files
PY_COUNT=$(find . -name "*.py" -not -path "./.git/*" | wc -l)
JSON_COUNT=$(find . -name "*.json" -not -path "./.git/*" | wc -l)
TOTAL_LINES=$(find . -name "*.py" -not -path "./.git/*" -exec cat {} \; 2>/dev/null | wc -l)

echo -e "${GREEN}📊 Statistics:${NC}"
echo "  Python files: $PY_COUNT"
echo "  JSON files: $JSON_COUNT"
echo "  Total Python lines: $TOTAL_LINES"

echo ""
echo -e "${GREEN}✅ SCORPION_BRAIN synced successfully!${NC}"
echo ""
echo "Location: $TARGET_DIR"
echo ""
echo "To update in the future, run:"
echo "  cd $TARGET_DIR && git pull"
echo ""
echo -e "${BLUE}🦂 The Scorpion King awaits...${NC}"

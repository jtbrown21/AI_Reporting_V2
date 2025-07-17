#!/bin/bash
# Headshot Sync Cron Job Setup
# This script should be run weekly to sync all client headshots

# Configuration
PROJECT_DIR="/Users/jtbrown/AgentInsider/AI_Reporting_V2"
VENV_PATH="$PROJECT_DIR/venv_new"
LOGS_DIR="$PROJECT_DIR/logs"
PYTHON_PATH="$VENV_PATH/bin/python3"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Log file with timestamp
LOG_FILE="$LOGS_DIR/headshot_sync_$(date +%Y%m%d).log"
CRON_LOG="$LOGS_DIR/cron.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Change to project directory
cd "$PROJECT_DIR" || {
    log "ERROR: Could not change to project directory: $PROJECT_DIR"
    exit 1
}

# Activate virtual environment and run sync
log "Starting weekly headshot sync..."
log "Project directory: $PROJECT_DIR"
log "Virtual environment: $VENV_PATH"
log "Log file: $LOG_FILE"

# Check if virtual environment exists
if [[ ! -d "$VENV_PATH" ]]; then
    log "ERROR: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Check if sync script exists
if [[ ! -f "scripts/headshot_sync.py" ]]; then
    log "ERROR: Headshot sync script not found at scripts/headshot_sync.py"
    exit 1
fi

# Run the sync script
log "Executing headshot sync script..."
source "$VENV_PATH/bin/activate" && "$PYTHON_PATH" scripts/headshot_sync.py

# Check exit code
if [[ $? -eq 0 ]]; then
    log "✅ Headshot sync completed successfully"
else
    log "❌ Headshot sync failed with exit code $?"
    exit 1
fi

# Log completion
log "Weekly headshot sync finished"

# Add summary to cron log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Weekly headshot sync completed" >> "$CRON_LOG"

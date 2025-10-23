#!/bin/bash

LOG_FILE="/home/datament/project/vinted/logs/cron.log"
LOG_DIR="/home/datament/project/vinted/logs"
DATE=$(date +%Y-%m-%d)
MAX_LOGS=7

if [ -f "$LOG_FILE" ]; then
    # Rotate the log file
    mv "$LOG_FILE" "$LOG_DIR/cron.log.$DATE"

    # Create a new empty log file
    touch "$LOG_FILE"

    # Delete old log files
    find "$LOG_DIR" -name "cron.log.*" -mtime +$MAX_LOGS -delete
fi
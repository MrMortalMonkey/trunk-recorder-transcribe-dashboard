#!/usr/bin/env bash

# -------------------------------------------------------
# Trunk Recorder Cleanup Script
#
# Removes old recordings to prevent disk usage from
# growing indefinitely.
#
# Default retention: 12 hours
# -------------------------------------------------------

RECORDINGS_DIR="/opt/trunk-recorder/station_name"
RETENTION_MINUTES=720
LOG_FILE="/var/log/trunk-recorder-cleanup.log"

echo "----------------------------------------" >> "$LOG_FILE"
echo "$(date) - Starting cleanup task" >> "$LOG_FILE"

# Delete directories older than retention window
find "$RECORDINGS_DIR" -mindepth 3 -type d -mmin +$RETENTION_MINUTES -print -exec rm -rf {} \; >> "$LOG_FILE" 2>&1

echo "$(date) - Cleanup complete" >> "$LOG_FILE"

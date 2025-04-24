#!/bin/bash
# Script to set up a cron job for the macOS Calendar Exporter

# Get the absolute path to the repository
REPO_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="${REPO_PATH}/examples/run-exporter.sh"

# Make sure the launcher script is executable
chmod +x "${SCRIPT_PATH}"

# Create a temporary file for the crontab
TEMP_CRONTAB=$(mktemp)

# Export the current crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# New crontab" > "$TEMP_CRONTAB"

# Check if the job already exists
if grep -q "mac-calendar-exporter" "$TEMP_CRONTAB"; then
    echo "Cron job for macOS Calendar Exporter already exists. Skipping."
else
    # Add the new job to run every 15 minutes
    echo "# macOS Calendar Exporter - run every 15 minutes" >> "$TEMP_CRONTAB"
    echo "*/15 * * * * ${SCRIPT_PATH} >> /tmp/mac-calendar-exporter.log 2>&1" >> "$TEMP_CRONTAB"
    
    # Install the new crontab
    crontab "$TEMP_CRONTAB"
    echo "Cron job installed to run every 15 minutes."
    echo "Logs will be written to /tmp/mac-calendar-exporter.log"
fi

# Clean up
rm "$TEMP_CRONTAB"

echo "To view scheduled cron jobs, use: crontab -l"
echo "To edit cron jobs, use: crontab -e"

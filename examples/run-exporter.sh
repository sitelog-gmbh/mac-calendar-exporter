#!/bin/bash
# Launcher script for macOS Calendar Exporter
# This script is meant to be executed by launchd or cron

# Stop on errors
set -e

# Set the script directory to the absolute path of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go to the project directory
cd "${SCRIPT_DIR}/.."
echo "Running from $(pwd)"

# Variables
VENV_DIR="venv"
LOG_FILE="/tmp/mac-calendar-exporter.log"

# Check for Python
if ! command -v python3 &> /dev/null; then
  echo "Python 3 not found. Please install Python 3." | tee -a "$LOG_FILE"
  exit 1
fi

# Ensure virtual environment exists and is working properly
setup_venv() {
  echo "Setting up virtual environment..." | tee -a "$LOG_FILE"
  
  # Remove venv if it exists but is broken
  if [ -d "$VENV_DIR" ]; then
    echo "Removing existing virtual environment..." | tee -a "$LOG_FILE"
    rm -rf "$VENV_DIR"
  fi
  
  # Create new environment
  echo "Creating new virtual environment..." | tee -a "$LOG_FILE"
  python3 -m venv "$VENV_DIR"
  
  # Install dependencies
  echo "Installing dependencies..." | tee -a "$LOG_FILE"
  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install -r requirements.txt
  "$VENV_DIR/bin/pip" install -e .
}

# Check if virtual environment exists and works
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
  setup_venv
else
  # Test if the venv has the required dependencies
  if ! "$VENV_DIR/bin/python" -c "import icalendar" &> /dev/null; then
    echo "Virtual environment is missing dependencies. Reinstalling..." | tee -a "$LOG_FILE"
    setup_venv
  fi
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

echo "Running macOS Calendar Exporter..." | tee -a "$LOG_FILE"
# Run the exporter with the venv python
"$VENV_DIR/bin/python" -m mac_calendar_exporter.main 2>&1 | tee -a "$LOG_FILE"

# Exit with the Python script's exit code
exit ${PIPESTATUS[0]}

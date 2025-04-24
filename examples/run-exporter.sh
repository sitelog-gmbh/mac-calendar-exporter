#!/bin/bash
# Launcher script for macOS Calendar Exporter
# This script is meant to be executed by launchd

# Set the script directory to the absolute path of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go to the project directory
cd "${SCRIPT_DIR}/.."
echo "Running from $(pwd)"

# Check if we're in a virtual environment
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
  # Activate the virtual environment
  source venv/bin/activate
else
  echo "Virtual environment not found"
fi

# Run the exporter
if [ -f "venv/bin/python" ]; then
  venv/bin/python -m mac_calendar_exporter.main
elif [ -f "venv/bin/python3" ]; then
  venv/bin/python3 -m mac_calendar_exporter.main
else
  echo "Could not find Python in virtual environment"
  # Try system python as fallback
  python3 -m mac_calendar_exporter.main
fi

# Exit with the Python script's exit code
exit $?

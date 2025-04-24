#!/bin/bash
# Setup and run script for macOS Calendar Exporter
# This script sets up a virtual environment, installs dependencies,
# and runs the macOS Calendar Exporter

# Stop on errors
set -e

# Variables
VENV_DIR="venv"
CONFIG_FILE=".env"
INTERACTIVE=true

# Check if --no-interactive flag is present
for arg in "$@"; do
  if [ "$arg" == "--no-interactive" ]; then
    INTERACTIVE=false
    echo "Running in non-interactive mode"
  fi
done

# Terminal colors
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${BLUE}===== macOS Calendar Exporter Setup and Run =====${NC}"

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check Python installation
if ! command_exists python3; then
  echo -e "${RED}Error: Python 3 not found. Please install Python 3 first.${NC}"
  exit 1
fi

echo -e "${GREEN}Python 3 found.${NC}"
python3 --version

# Check calendar access tools
echo -e "\n${BLUE}Checking calendar access tools...${NC}"

# Check mcal
if command_exists mcal; then
  echo -e "${GREEN}mcal found.${NC} $(mcal --version 2>&1 | head -n 1)"
else
  echo -e "${YELLOW}mcal not found. Consider installing it with 'brew install mcal'${NC}"
  echo -e "${YELLOW}Setting up mock data for now...${NC}"
  
  # Check if mock mode is set in config
  if [ -f "$CONFIG_FILE" ]; then
    if ! grep -q "CALENDAR_TYPE=mock" "$CONFIG_FILE"; then
      echo "CALENDAR_TYPE=mock" >> "$CONFIG_FILE"
      echo -e "${YELLOW}Added CALENDAR_TYPE=mock to $CONFIG_FILE${NC}"
    fi
  fi
fi

# Check icalBuddy
if command_exists icalBuddy; then
  echo -e "${GREEN}icalBuddy found.${NC} $(icalBuddy -V)"
else
  echo -e "${YELLOW}icalBuddy not found. Consider installing it with 'brew install icalbuddy'${NC}"
fi

# Create or update virtual environment
if [ ! -d "$VENV_DIR" ]; then
  echo -e "\n${BLUE}Creating virtual environment...${NC}"
  python3 -m venv "$VENV_DIR"
else
  echo -e "\n${GREEN}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Install or upgrade pip
echo -e "\n${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo -e "\n${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt

# Install the package in development mode
echo -e "\n${BLUE}Installing macOS Calendar Exporter in development mode...${NC}"
pip install -e .

# Check for config file
if [ ! -f "$CONFIG_FILE" ]; then
  echo -e "\n${YELLOW}Config file not found. Creating from example...${NC}"
  if [ -f ".env.example" ]; then
    cp .env.example "$CONFIG_FILE"
    echo -e "${GREEN}Created $CONFIG_FILE from example. Please edit it with your settings.${NC}"
  else
    echo -e "${RED}Error: .env.example not found.${NC}"
    touch "$CONFIG_FILE"
    echo "# macOS Calendar Exporter Configuration" > "$CONFIG_FILE"
    echo "CALENDAR_TYPE=mcal" >> "$CONFIG_FILE" 
    echo "CALENDAR_NAMES=Calendar" >> "$CONFIG_FILE"
    echo "DAYS_AHEAD=30" >> "$CONFIG_FILE"
    echo "ICS_FILE=./calendar_export.ics" >> "$CONFIG_FILE"
    echo "USE_MOCK_ON_FAILURE=true" >> "$CONFIG_FILE"
    echo "ENABLE_SFTP=false" >> "$CONFIG_FILE"
    echo -e "${GREEN}Created basic $CONFIG_FILE. Please edit it with your settings.${NC}"
  fi
else
  echo -e "\n${GREEN}Config file $CONFIG_FILE found.${NC}"
fi

# Run calendar access test
echo -e "\n${BLUE}Testing calendar access...${NC}"
python -c "
try:
    from mac_calendar_exporter.main import MacCalendarExporter
    exporter = MacCalendarExporter()
    calendar_accessor = exporter._get_calendar_accessor()
    if calendar_accessor:
        print('\033[0;32mCalendar accessor initialized successfully.\033[0m')
        calendars = calendar_accessor.list_calendars()
        print(f'Found {len(calendars)} calendars:')
        for cal in calendars:
            print(f'  - {cal[\"title\"]}')
    else:
        print('\033[0;33mUsing mock data.\033[0m')
except Exception as e:
    print(f'\033[0;31mError testing calendar access: {e}\033[0m')
"

# Ask user if they want to run the exporter (only in interactive mode)
if [ "$INTERACTIVE" = true ]; then
  echo -e "\n${BLUE}Do you want to run the macOS Calendar Exporter now? (y/n)${NC}"
  read -r run_exporter
  
  if [[ $run_exporter =~ ^[Yy]$ ]]; then
    run_it=true
  else
    run_it=false
    echo -e "\n${YELLOW}Skipping execution.${NC}"
    echo -e "You can run the exporter later with: python -m mac_calendar_exporter.main"
  fi
else
  # In non-interactive mode, always run the exporter
  run_it=true
fi

if [ "$run_it" = true ]; then
  echo -e "\n${BLUE}Running macOS Calendar Exporter...${NC}"
  python -m mac_calendar_exporter.main
  
  # Check exit status
  if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}macOS Calendar Exporter completed successfully.${NC}"
  else
    echo -e "\n${RED}macOS Calendar Exporter encountered errors.${NC}"
    echo -e "Check the logs above for details."
  fi
else
  echo -e "\n${YELLOW}Skipping execution.${NC}"
  echo -e "You can run the exporter later with: python -m mac_calendar_exporter.main"
fi

echo -e "\n${BLUE}===== Setup Complete =====${NC}"
echo -e "To use the macOS Calendar Exporter in the future, activate the virtual environment:"
echo -e "  source $VENV_DIR/bin/activate"
echo -e "Then run:"
echo -e "  python -m mac_calendar_exporter.main"

# Deactivate virtual environment
deactivate

exit 0

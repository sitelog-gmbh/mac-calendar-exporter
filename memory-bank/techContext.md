# Technical Context

## Technologies Used

### Core Technologies
- **Python 3.7+**: Primary programming language
- **Swift with EventKit**: For accessing macOS Calendar database
- **icalendar**: Python library for generating ICS files with timezone support
- **paramiko**: Python library for SFTP operations
- **python-dotenv**: For environment-based configuration management
- **click**: CLI framework for user interface
- **launchd**: macOS service manager for automated scheduling

### Development Tools
- **pytest**: For test automation
- **black**: Code formatter
- **isort**: Import sorter
- **flake8**: Linting
- **pre-commit**: Git hooks for code quality
- **venv**: Python virtual environment

## Technical Requirements

### System Requirements
- macOS 10.15+ (Catalina or newer)
- Python 3.9+
- Local Calendar app with synchronized accounts
- SFTP server credentials with write access
- Network access to SFTP server

### Dependencies
```
icalendar~=5.0.4
paramiko~=3.0.0
keyring~=23.13.1
click~=8.1.3
python-dotenv~=1.0.0
```

## Development Setup

### Local Development Environment
1. Clone repository
2. Create and activate virtual environment: `python -m venv venv && source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install -r requirements-dev.txt`
5. Configure environment variables in `.env` file (see `.env.example`)

### Configuration
Configuration is stored in a combination of:
1. Command line arguments for one-time overrides
2. Environment variables for sensitive information
3. Configuration file for persistent settings

## Security Considerations
- Credentials are stored in macOS Keychain using the keyring library
- SFTP connections use key-based authentication when possible
- Minimal permissions are requested for calendar access
- No sensitive information is logged

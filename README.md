# macOS Calendar Exporter

Export calendar events from macOS to ICS files and upload to a SFTP server.

## Overview

macOS Calendar Exporter is a Python tool specifically designed to export events from Mac calendars. It generates ICS files containing your calendar events and can automatically upload them to an SFTP server, making it perfect e.g. for Home Assistant integration without needing direct API access to calendar services.

## Features

- **Mac Calendar Access**: Uses macOS Swift EventKit to access your calendars
- **Timezone Support**: Properly handles european timezones (CET/CEST)
- **Privacy Mode**: Only exports event titles and times by default (descriptions optional)
- **SFTP Upload**: Automatically uploads to your specified server
- **Local Calendar Import**: Directly import exported events back into a local/iCloud macOS calendar

## Installation

### Prerequisites

- macOS with Calendar app
- Python 3.7+
- Any calendar synced with macOS Calendar app
- Calendar app permissions enabled for Terminal/VSCode

### Setup

1. Clone this repository:

```bash
git clone https://github.com/nodomain/mac-calendar-exporter.git
cd mac-calendar-exporter
```

1. Use the setup script to install and configure:

```bash
./setup-and-run.sh
```

This will:

- Create a virtual environment
- Install required packages
- Configure your settings
- Run an initial export

## Configuration

Edit the `.env` file to customize your settings:

| Setting | Description | Default | Required |
|---------|-------------|---------|----------|
| `CALENDAR_NAMES` | Comma-separated list of calendar names to export | `Calendar` | No |
| `DAYS_AHEAD` | Number of days ahead to export events for | `30` | No |
| `ICS_FILE` | Path to output ICS file | `./calendar_export.ics` | No |
| `ICS_CALENDAR_NAME` | Name of the calendar in the ICS file | `Exported Calendar` | No |
| `INCLUDE_DETAILS` | Include event descriptions and locations | `false` | No |
| `TITLE_LENGTH_LIMIT` | Maximum length for event titles (0 for unlimited) | `36` | No |
| `ENABLE_SFTP` | Enable SFTP upload | `false` | No |
| `SFTP_HOST` | SFTP server hostname | | Yes, if SFTP enabled |
| `SFTP_PORT` | SFTP server port | `22` | No |
| `SFTP_USERNAME` | SFTP username | | Yes, if SFTP enabled |
| `SFTP_PASSWORD` | SFTP password | | Yes, if no key file |
| `SFTP_KEY_FILE` | Path to SSH private key for SFTP | | Yes, if no password |
| `SFTP_REMOTE_PATH` | Remote path to upload file to (including filename) | | Yes, if SFTP enabled |
| `LOCAL_IMPORT_CALENDAR` | Local macOS calendar name for direct import | | No |
| `LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` | No |

## Usage

### Command Line

Run the exporter manually:

```bash
./setup-and-run.sh
```

Or directly using Python:

```bash
python -m mac_calendar_exporter.main
```

### Scheduling with Cron (Recommended)

Set up automatic exports on a schedule using cron (more reliable than launchd):

1. **Use the provided setup script:**

```bash
./examples/cron-setup.sh
```

This script will:
- Create a cron job that runs every 15 minutes
- Make sure the run-exporter.sh script is executable
- Set up logging to `/tmp/mac-calendar-exporter.log`

2. **Verify the cron job was created:**

```bash
crontab -l
```

3. **To edit the schedule manually:**

```bash
crontab -e
```

Then modify the timing pattern. For example:
- `*/15 * * * *` = every 15 minutes
- `0 */1 * * *` = hourly
- `0 4 * * *` = daily at 4am

### Alternative Scheduling with launchd

macOS also provides launchd, but it can be more complex to set up correctly:

1. **Copy the example plist file:**

```bash
cp examples/cc.nodomain.mac-calendar-exporter.plist ~/Library/LaunchAgents/
```

2. **Edit the file to use absolute paths:**

```bash
nano ~/Library/LaunchAgents/cc.nodomain.mac-calendar-exporter.plist
```

3. **Try loading with:**

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/cc.nodomain.mac-calendar-exporter.plist
```

Note: Modern macOS versions are more restrictive with launchd jobs. If you encounter issues, use the cron scheduling method instead.

## Troubleshooting

### macOS Launchd Restrictions

Recent versions of macOS have stricter security restrictions on launchd jobs. If you encounter issues loading the plist file:

1. **Try a simple test job first**:
   ```bash
   cp examples/test-launchd.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/test-launchd.plist
   ```

2. **Use full paths in your plist file**:
   ```xml
   <string>/Users/YOUR_USERNAME/src/mac-calendar-exporter/examples/run-exporter.sh</string>
   ```

3. **For modern macOS**, the legacy `launchctl load` command may not work. Try:
   ```bash
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/cc.nodomain.mac-calendar-exporter.plist
   ```

4. **To see detailed error messages**, run as root:
   ```bash
   sudo launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/cc.nodomain.mac-calendar-exporter.plist
   ```

5. **As an alternative** to launchd, consider using `crontab`:
   ```bash
   crontab -e
   # Then add this line to run every 15 minutes:
   */15 * * * * /Users/YOUR_USERNAME/src/mac-calendar-exporter/examples/run-exporter.sh
   ```

### Calendar Permission Issues

Make sure you've granted permission for Terminal/VSCode to access the Calendar app:

1. Go to System Settings > Privacy & Security > Calendar
2. Enable access for Terminal, VSCode, or other apps you use to run the exporter

### SFTP Connection Issues

- Check that your SFTP server is running and accessible
- Verify credentials (username/password)
- Make sure your SFTP_REMOTE_PATH includes the filename (e.g., `/path/to/directory/calendar.ics`)
- Test the connection manually: `sftp username@hostname`

### Launchd Scheduling Issues

If you encounter issues with the launchd job not running correctly:

1. Check the error logs in `/tmp/mac-calendar-exporter.err` and `/tmp/mac-calendar-exporter.out`
2. Make sure the launcher script has the correct permissions: `chmod +x examples/run-exporter.sh`
3. Check that the `WorkingDirectory` in the plist file is set to your actual project path
4. Verify the Python virtual environment is properly set up and activated by the launcher script
5. Try running the launcher script manually to test: `./examples/run-exporter.sh`

## Local Calendar Import

In addition to uploading to an SFTP server, you can import the exported events directly back into a local macOS calendar. This is useful for:

- Creating a filtered/cleaned view of your calendars
- Syncing events between different calendar sources
- Creating a backup calendar with limited event details

### Setup

1. **Create a dedicated calendar** in the macOS Calendar app (e.g., "Exported Events")

2. **Configure the local import calendar** in your `.env` file:

```bash
LOCAL_IMPORT_CALENDAR=Exported Events
```

3. **Disable SFTP** (or leave it unconfigured) if you only want local import:

```bash
ENABLE_SFTP=false
```

### How It Works

When `LOCAL_IMPORT_CALENDAR` is configured and SFTP is not configured:

1. The exporter extracts events from your source calendars
2. Generates an ICS file with the exported events
3. **Deletes all existing events** in the target calendar (within the configured date range)
4. **Imports the new events** from the ICS file into the target calendar

**Important Notes:**

- The target calendar must exist in your macOS Calendar app
- The target calendar must be writable (not read-only)
- All events in the target calendar within the date range will be deleted before import
- If both SFTP and local import are configured, SFTP takes priority

## Integration with Home Assistant

1. Upload the ICS file to your Home Assistant server using SFTP
2. Configure the Calendar integration in Home Assistant:

```yaml
# configuration.yaml
calendar:
  - platform: ics
    name: Office Calendar
    url: /config/www/calendar.ics
```

## License

MIT

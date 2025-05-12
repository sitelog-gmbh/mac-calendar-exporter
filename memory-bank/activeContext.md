# Active Context

## Current Implementation Status
We've successfully implemented the macOS Calendar Exporter which now:

1. Accesses calendar data via macOS Swift's EventKit API
2. Exports selected calendars to an ICS file with proper timezone support
3. Uploads the ICS file to an SFTP server
4. Provides configuration through environment variables
5. Supports automated scheduling via launchd

## Recent Achievements

### Calendar Access Method
We've implemented a Swift-based EventKit approach that directly accesses the macOS Calendar database. This proved to be more reliable than the initially considered AppleScript method. The solution works with any calendars that are synced with macOS Calendar app.

### Timezone Handling
We've implemented proper timezone support for Europe/Berlin (CET/CEST) by adding VTIMEZONE components to the ICS file. This fixed the 2-hour timezone discrepancy in Home Assistant.

### Privacy Enhancement
We've configured the exporter to include only event titles and times by default, with an optional setting to include full details like descriptions and locations. This protects sensitive information while still providing calendar functionality.

### Security Approach
We're using paramiko for secure SFTP connections with support for both password and key-based authentication.

### Automated Scheduling
We've implemented scheduling using launchd with a customizable plist file. The scheduler runs at 4am by default, but can be configured for multiple runs per day.

## Current Configuration

### Calendar Selection
Users can specify which calendars to export via the `CALENDAR_NAMES` setting in the `.env` file, supporting multiple calendars.

### Date Range
We're using a rolling window approach, exporting events from today plus a configurable number of days ahead (default: 30 days).

### ICS File Format
The ICS file includes:
- Proper timezone information for Europe/Berlin
- Event titles and times (with optional length limiting to avoid line breaks)
- Optional descriptions and locations (disabled by default)
- Calendar categorization

### Title Length Limiting
We've implemented title length limiting with a default of 36 characters to prevent line breaks in Home Assistant dashboards. This ensures a clean display while still providing enough context for each event. When titles exceed the limit, they're truncated and an ellipsis is added for clarity.

## Next Steps
1. Consider adding filtering options for events
2. Explore improved error handling and recovery
3. Add logging to file for better troubleshooting
4. Consider multi-calendar exports to separate files

# macOS Calendar Exporter Project Brief

## Overview
A utility to export calendar entries from the macOS Calendar app to an ICS file, and upload this file to an SFTP server. This enables calendar integration with Home Assistant without requiring direct calendar API access.

## Core Requirements
1. Access calendar data from local macOS Calendar app using Swift's EventKit
2. Export calendar entries to standard ICS format
3. Securely upload ICS file to an SFTP server
4. Enable scheduling for automated regular exports
5. Provide configuration options for calendar selection, date ranges, etc.

## Constraints
1. Cannot use direct calendar API access due to corporate policies
2. Must work with locally synced calendar data on macOS
3. Solution must be secure, particularly for SFTP credentials

## Success Criteria
1. Calendar entries successfully exported to valid ICS format
2. ICS file successfully uploaded to specified SFTP server
3. Home Assistant able to display calendar entries from uploaded ICS file
4. Process can run automatically on a schedule
5. Minimal manual intervention required after initial setup

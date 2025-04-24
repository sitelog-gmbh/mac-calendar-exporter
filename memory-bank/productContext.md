# Product Context

## Problem Statement
Users with corporate calendars often face restrictions accessing their calendar data through APIs due to security policies. Yet, they still need to display this calendar data in external systems like Home Assistant for personal automation and information dashboards.

## Solution Overview
CalDAV Exporter bridges this gap by leveraging Swift's EventKit to access the local macOS Calendar app to export calendar entries to an ICS file format with proper timezone support. This file is then uploaded to an SFTP server where Home Assistant can access it without requiring direct API integration with corporate calendar systems.

## User Experience Goals
1. **Minimal Setup**: Simple configuration for calendar selection, SFTP details, and scheduling
2. **Reliability**: Consistent exports on schedule without manual intervention
3. **Completeness**: All relevant calendar information properly exported and displayed
4. **Security**: Credentials stored securely, with no exposure of sensitive information
5. **Flexibility**: Options to customize what calendars are exported and date ranges

## Use Cases
1. **Regular Syncing**: Automated daily/hourly export of calendar entries to keep Home Assistant updated
2. **Manual Export**: On-demand export and upload when immediate updates are needed
3. **Calendar Selection**: Ability to include or exclude specific calendars from export
4. **Range Selection**: Export only upcoming events or specify a date range

#!/usr/bin/env python3
"""
ICS Generator Module.

This module generates ICS files from calendar events using the icalendar package.
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Union

from icalendar import Calendar, Event, vCalAddress, vText

logger = logging.getLogger(__name__)


class ICSGenerator:
    """Generate ICS files from calendar events."""

    def __init__(self):
        """Initialize the ICSGenerator class."""
        pass

    def generate_ics(
        self, 
        events: List[Dict], 
        calendar_name: str = "Exported Calendar",
        output_file: Optional[str] = None,
        include_details: bool = False,
        title_length_limit: int = 36  # Default to 50 characters
    ) -> str:
        """
        Generate an ICS file from the provided events.
        
        Args:
            events: List of event dictionaries from MacOSCalendarAccess
            calendar_name: Name to use for the calendar in the ICS file
            output_file: Path to save the ICS file (if None, uses temp file)
            
        Returns:
            str: Path to the generated ICS file
        """
        logger.info(f"Generating ICS file with {len(events)} events")
        
        # Create calendar
        cal = Calendar()
        cal.add('prodid', '-//macOS Calendar Exporter//mac-calendar-exporter//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', calendar_name)
        # Add timezone information for Europe/Berlin (CEST/CET)
        cal.add('x-wr-timezone', 'Europe/Berlin')
        
        # Add a VTIMEZONE component for Europe/Berlin
        tz = self._create_timezone_component()
        cal.add_component(tz)
        
        # Add events to calendar
        for event_data in events:
            event = self._create_event_from_dict(event_data, include_details, title_length_limit)
            if event:
                cal.add_component(event)
        
        # Determine output file
        if output_file is None:
            fd, output_file = tempfile.mkstemp(suffix='.ics')
            os.close(fd)
        
        # Write calendar to file
        with open(output_file, 'wb') as f:
            f.write(cal.to_ical())
        
        # Post-process the file to ensure titles are correctly truncated
        if title_length_limit > 0:
            self._post_process_ics_file(output_file, title_length_limit)
        
        logger.info(f"ICS file generated at {output_file}")
        return output_file
    
    def _post_process_ics_file(self, file_path: str, title_length_limit: int) -> None:
        """
        Post-process the ICS file to ensure titles are correctly truncated.
        
        Args:
            file_path: Path to the ICS file
            title_length_limit: Maximum length for event titles
        """
        try:
            # Read the file with explicit UTF-8 encoding
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Process lines
            for i, line in enumerate(lines):
                if line.startswith('SUMMARY:'):
                    title = line[len('SUMMARY:'):].strip()
                    if len(title) > title_length_limit:
                        # Use three periods for ellipsis to ensure compatibility
                        truncated = title[:title_length_limit] + '...'
                        lines[i] = f'SUMMARY:{truncated}\n'
                        logger.debug(f"Post-processing truncated: '{title}' → '{truncated}'")
            
            # Write back to file with explicit UTF-8 encoding
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            logger.info(f"Post-processed {file_path} to ensure title lengths are limited to {title_length_limit} characters")
        except Exception as e:
            logger.error(f"Error post-processing ICS file: {e}")

    def _create_event_from_dict(self, event_data: Dict, include_details: bool = False, title_length_limit: int = 0) -> Optional[Event]:
        """
        Create an iCalendar Event from an event dictionary.
        
        Args:
            event_data: Dictionary with event data from MacOSCalendarAccess
            include_details: Whether to include description and location details
            title_length_limit: Maximum length for event titles (0 for unlimited)
            
        Returns:
            Optional[Event]: iCalendar Event object or None if creation fails
        """
        try:
            event = Event()
            
            # Basic event properties
            title = event_data['title']
            original_title = title
            
            # Apply title length limit if specified
            if title_length_limit > 0 and len(title) > title_length_limit:
                truncated_title = title[:title_length_limit] + '…'  # Using proper ellipsis character
                logger.info(f"Truncated title: '{original_title}' → '{truncated_title}'")
                
                # Replace the title in the event_data to ensure consistency
                event_data['title'] = truncated_title
                
                # Use the truncated title directly
                event.add('summary', truncated_title)
            else:
                event.add('summary', title)
            event.add('uid', event_data['event_id'])
            
            # Handle start and end dates
            try:
                # MacOS Calendar returns dates in a format like: 
                # "date Saturday, November 13, 2021 at 9:00:00 AM"
                # We need to parse this format
                start_date = self._parse_macos_date(event_data['start_date'])
                end_date = self._parse_macos_date(event_data['end_date'])
                
                if event_data.get('all_day', False):
                    event.add('dtstart', start_date.date())
                    event.add('dtend', end_date.date())
                else:
                    event.add('dtstart', start_date)
                    event.add('dtend', end_date)
            except Exception as e:
                logger.error(f"Failed to parse dates for event {event_data['title']}: {e}")
                return None
            
            # Optional event properties - only include if requested
            if include_details:
                if event_data.get('description'):
                    event.add('description', event_data['description'])
                    
                if event_data.get('location'):
                    event.add('location', event_data['location'])
            
            # Add calendar name as category
            if event_data.get('calendar_name'):
                event.add('categories', event_data['calendar_name'])
            
            return event
        except Exception as e:
            logger.error(f"Failed to create event {event_data.get('title', 'unknown')}: {e}")
            return None
    
    def _parse_macos_date(self, date_string: str) -> datetime:
        """
        Parse a date string from the MacOS Calendar format.
        
        Args:
            date_string: Date string from MacOS Calendar
            
        Returns:
            datetime: Parsed datetime object
            
        Example input: "date Saturday, November 13, 2021 at 9:00:00 AM"
        """
        # Remove the "date " prefix if present
        if date_string.startswith("date "):
            date_string = date_string[5:]
            
        # Try multiple date formats that might be returned by AppleScript
        formats = [
            "%A, %B %d, %Y at %I:%M:%S %p",  # Saturday, November 13, 2021 at 9:00:00 AM
            "%Y-%m-%d %H:%M:%S %z",          # 2021-11-13 09:00:00 +0100
            "%Y-%m-%dT%H:%M:%S%z",           # 2021-11-13T09:00:00+0100
            "%Y-%m-%d %H:%M:%S",             # 2021-11-13 09:00:00
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # If none of the formats match, try a more flexible approach
        # This handles formats like "Saturday, November 13, 2021 at 9:00:00 AM"
        try:
            import dateutil.parser
            return dateutil.parser.parse(date_string)
        except:
            logger.error(f"Failed to parse date: {date_string}")
            raise ValueError(f"Cannot parse date format: {date_string}")
            
    def _create_timezone_component(self):
        """
        Create a VTIMEZONE component for Europe/Berlin.
        
        Returns:
            A VTIMEZONE component for Europe/Berlin with both standard and daylight time
        """
        from icalendar import Timezone, TimezoneStandard, TimezoneDaylight
        
        tz = Timezone()
        tz.add('tzid', 'Europe/Berlin')
        
        from datetime import timedelta
        
        # Standard time (CET)
        standard = TimezoneStandard()
        standard.add('dtstart', datetime(1970, 10, 25, 3, 0, 0))
        standard.add('tzoffsetfrom', timedelta(hours=2))  # From CEST (+0200)
        standard.add('tzoffsetto', timedelta(hours=1))    # To CET (+0100)
        standard.add('tzname', 'CET')
        standard.add('rrule', {'freq': 'yearly', 'bymonth': 10, 'byday': '-1su'})  # Last Sunday in October
        
        # Daylight saving time (CEST)
        daylight = TimezoneDaylight()
        daylight.add('dtstart', datetime(1970, 3, 29, 2, 0, 0))
        daylight.add('tzoffsetfrom', timedelta(hours=1))  # From CET (+0100)
        daylight.add('tzoffsetto', timedelta(hours=2))    # To CEST (+0200)
        daylight.add('tzname', 'CEST')
        daylight.add('rrule', {'freq': 'yearly', 'bymonth': 3, 'byday': '-1su'})   # Last Sunday in March
        
        tz.add_component(standard)
        tz.add_component(daylight)
        
        return tz


if __name__ == "__main__":
    # Simple test function when run directly
    logging.basicConfig(level=logging.INFO)
    
    from mac_calendar_exporter.calendar.eventkit_calendar import EventKitCalendarAccess
    
    # Get sample events
    calendar = EventKitCalendarAccess()
    events = calendar.get_events(days_ahead=7)
    
    # Generate ICS file
    generator = ICSGenerator()
    ics_file = generator.generate_ics(events, "Test Calendar")
    
    print(f"Generated ICS file: {ics_file}")

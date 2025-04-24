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
        include_details: bool = False
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
            event = self._create_event_from_dict(event_data, include_details)
            if event:
                cal.add_component(event)
        
        # Determine output file
        if output_file is None:
            fd, output_file = tempfile.mkstemp(suffix='.ics')
            os.close(fd)
        
        # Write calendar to file
        with open(output_file, 'wb') as f:
            f.write(cal.to_ical())
        
        logger.info(f"ICS file generated at {output_file}")
        return output_file

    def _create_event_from_dict(self, event_data: Dict, include_details: bool = False) -> Optional[Event]:
        """
        Create an iCalendar Event from an event dictionary.
        
        Args:
            event_data: Dictionary with event data from MacOSCalendarAccess
            include_details: Whether to include description and location details
            
        Returns:
            Optional[Event]: iCalendar Event object or None if creation fails
        """
        try:
            event = Event()
            
            # Basic event properties
            event.add('summary', event_data['title'])
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

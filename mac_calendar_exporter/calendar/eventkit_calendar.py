#!/usr/bin/env python3
"""
EventKit Calendar Access Module.

This module provides access to calendar data using Swift's EventKit framework.
It works by executing a Swift script that interfaces with EventKit and returns
JSON data with calendar information and events.
"""

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EventKitCalendarAccess:
    """Access calendar data from macOS Calendar app using EventKit via Swift."""

    def __init__(self):
        """Initialize the EventKitCalendarAccess class."""
        logger.info("Initializing EventKit calendar access")
        self.script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "eventkit_calendar.swift"
        )
        logger.info(f"Using EventKit script at: {self.script_path}")
        
        # Ensure script is executable
        if not os.access(self.script_path, os.X_OK):
            os.chmod(self.script_path, 0o755)
            logger.info("Set execute permissions on EventKit script")

    def list_calendars(self) -> List[Dict[str, str]]:
        """
        Get a list of available calendars.
        
        Returns:
            List[Dict[str, str]]: List of dictionaries with calendar info
        """
        try:
            # Run the Swift script with --calendars operation
            result = self._run_script(["--calendars"])
            
            if not result or "error" in result:
                error_msg = result.get("error", "Unknown error") if result else "No result from script"
                logger.error(f"Failed to list calendars: {error_msg}")
                return []
            
            # Process the returned calendar list
            calendars_data = result.get("calendars", [])
            
            # Convert to the standard format used by other modules
            calendars = []
            for cal in calendars_data:
                calendar_dict = {
                    "title": cal.get("title", "Unknown"),
                    "id": cal.get("id", ""),
                    "type": cal.get("type", ""),
                    "source": cal.get("source", "")
                }
                calendars.append(calendar_dict)
                
            logger.info(f"Found {len(calendars)} calendars using EventKit")
            return calendars
        except Exception as e:
            logger.error(f"Failed to list calendars using EventKit: {e}")
            return []

    def get_events(
        self, 
        calendar_names: Optional[List[str]] = None, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days_ahead: Optional[int] = 30
    ) -> List[Dict]:
        """
        Get events from specified calendars within the given date range.
        
        Args:
            calendar_names: List of calendar names to fetch events from. 
                           If None, all calendars are used.
            start_date: Start date for events. If None, today is used.
            end_date: End date for events. If None, calculated from days_ahead.
            days_ahead: Number of days ahead to fetch events if end_date is None.
            
        Returns:
            List[Dict]: List of event dictionaries
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date is None and days_ahead is not None:
            end_date = start_date + timedelta(days=days_ahead)
        
        try:
            # Prepare arguments for the Swift script
            args = ["--events"]
            
            # Add date range
            args.extend([
                "--start-date", start_date.strftime("%Y-%m-%d"),
                "--end-date", end_date.strftime("%Y-%m-%d")
            ])
            
            # Add calendar filter if provided
            if calendar_names and len(calendar_names) > 0:
                # Currently, the Swift script only supports filtering by a single calendar
                # If multiple calendars are provided, we'll query each and combine the results
                all_events = []
                
                for calendar_name in calendar_names:
                    logger.info(f"Getting events for calendar: {calendar_name}")
                    calendar_args = args + ["--calendar", calendar_name]
                    
                    result = self._run_script(calendar_args)
                    
                    if not result or "error" in result:
                        error_msg = result.get("error", "Unknown error") if result else "No result from script"
                        logger.warning(f"Failed to get events for calendar {calendar_name}: {error_msg}")
                        continue
                    
                    events_data = result.get("events", [])
                    all_events.extend(events_data)
                
                logger.info(f"Retrieved {len(all_events)} events from {len(calendar_names)} calendars")
                return all_events
            else:
                # Get events from all calendars
                logger.info("Getting events from all calendars")
                result = self._run_script(args)
                
                if not result or "error" in result:
                    error_msg = result.get("error", "Unknown error") if result else "No result from script"
                    logger.error(f"Failed to get events: {error_msg}")
                    return []
                
                events_data = result.get("events", [])
                logger.info(f"Retrieved {len(events_data)} events from all calendars")
                return events_data
                
        except Exception as e:
            logger.error(f"Failed to get events using EventKit: {e}")
            return []
            
    def _run_script(self, args: List[str]) -> Optional[Dict]:
        """
        Run the Swift script with provided arguments.
        
        Args:
            args: List of arguments to pass to the script
            
        Returns:
            Optional[Dict]: Parsed JSON output from the script, or None if failed
        """
        try:
            # Use explicit Swift path to ensure it works in cron environment
            swift_path = "/usr/bin/swift"
            if not os.path.exists(swift_path):
                # Try alternative path
                swift_path = subprocess.run(
                    ["which", "swift"],
                    capture_output=True,
                    text=True
                ).stdout.strip()
                if not swift_path:
                    logger.error("Swift not found in PATH")
                    return None
            
            cmd = [swift_path, self.script_path] + args
            
            # Execute the Swift script
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=30  # Add timeout to prevent hanging
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"Swift script returned error code {result.returncode}: {error_msg}")
                if result.stdout:
                    logger.error(f"Swift script stdout: {result.stdout[:500]}")  # Log first 500 chars
                return None
            
            # Check if stdout is empty
            if not result.stdout.strip():
                logger.error("Swift script returned empty output")
                if result.stderr:
                    logger.error(f"Swift script stderr: {result.stderr}")
                return None
            
            # Parse JSON output
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON output from Swift script: {e}")
                logger.error(f"Raw stdout (first 1000 chars): {result.stdout[:1000]}")
                if result.stderr:
                    logger.error(f"Raw stderr: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Swift script timed out after 30 seconds")
            return None
        except Exception as e:
            logger.error(f"Failed to run Swift script: {e}")
            return None


if __name__ == "__main__":
    # Simple test function when run directly
    logging.basicConfig(level=logging.DEBUG)
    calendar = EventKitCalendarAccess()
    print("Available calendars:")
    calendars = calendar.list_calendars()
    for cal in calendars:
        print(f" - {cal['title']} ({cal.get('type', '')})")
        
    print("\nEvents for next 7 days:")
    events = calendar.get_events(days_ahead=7)
    for event in events:
        print(f" - {event['title']} ({event['start_date']})")
        if event.get('location'):
            print(f"   Location: {event['location']}")

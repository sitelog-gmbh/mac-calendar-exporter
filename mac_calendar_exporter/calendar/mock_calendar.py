#!/usr/bin/env python3
"""
Mock Calendar Data Module.

This module provides mock calendar data for testing or when Calendar app access fails.
"""

import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class MockCalendarData:
    """Generate mock calendar entries for testing."""
    
    @staticmethod
    def get_mock_calendars() -> List[Dict[str, str]]:
        """
        Return a list of mock calendars.
        
        Returns:
            List[Dict[str, str]]: List of dictionaries with calendar info
        """
        return [
            {"title": "Work"},
            {"title": "Personal"},
            {"title": "Family"},
            {"title": "Calendar"}
        ]
    
    @staticmethod
    def get_mock_events(
        calendar_names: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days_ahead: Optional[int] = 30
    ) -> List[Dict]:
        """
        Generate mock events.
        
        Args:
            calendar_names: List of calendar names to generate events for
            start_date: Start date for events
            end_date: End date for events
            days_ahead: Number of days ahead to generate events
            
        Returns:
            List[Dict]: List of mock event dictionaries
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date is None and days_ahead is not None:
            end_date = start_date + timedelta(days=days_ahead)
            
        if not calendar_names:
            calendar_names = ["Calendar"]
            
        # Generate some standard event types
        events = []
        cal_name = calendar_names[0]  # Use first calendar name
        
        # Add events for each day in the range
        current_date = start_date
        event_id = 1
        
        while current_date <= end_date:
            # Morning meeting every weekday
            if current_date.weekday() < 5:  # Monday to Friday
                meeting_start = datetime.combine(current_date.date(), time(9, 0))
                meeting_end = datetime.combine(current_date.date(), time(10, 0))
                events.append({
                    "event_id": f"event-{event_id}",
                    "calendar_name": cal_name,
                    "title": "Morning Team Meeting",
                    "location": "Conference Room",
                    "description": "Daily team sync-up",
                    "start_date": meeting_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_date": meeting_end.strftime("%Y-%m-%d %H:%M:%S"),
                    "all_day": False
                })
                event_id += 1
            
            # Lunch every day
            lunch_start = datetime.combine(current_date.date(), time(12, 0))
            lunch_end = datetime.combine(current_date.date(), time(13, 0))
            events.append({
                "event_id": f"event-{event_id}",
                "calendar_name": cal_name,
                "title": "Lunch Break",
                "location": "",
                "description": "",
                "start_date": lunch_start.strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": lunch_end.strftime("%Y-%m-%d %H:%M:%S"),
                "all_day": False
            })
            event_id += 1
            
            # Weekly review on Fridays
            if current_date.weekday() == 4:  # Friday
                review_start = datetime.combine(current_date.date(), time(15, 0))
                review_end = datetime.combine(current_date.date(), time(16, 0))
                events.append({
                    "event_id": f"event-{event_id}",
                    "calendar_name": cal_name,
                    "title": "Weekly Review",
                    "location": "Main Conference Room",
                    "description": "Review of the week's progress",
                    "start_date": review_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_date": review_end.strftime("%Y-%m-%d %H:%M:%S"),
                    "all_day": False
                })
                event_id += 1
                
            # Weekend events
            if current_date.weekday() == 5:  # Saturday
                events.append({
                    "event_id": f"event-{event_id}",
                    "calendar_name": cal_name,
                    "title": "Weekend Brunch",
                    "location": "Cafe Central",
                    "description": "Brunch with friends",
                    "start_date": current_date.strftime("%Y-%m-%d"),
                    "end_date": current_date.strftime("%Y-%m-%d"),
                    "all_day": True
                })
                event_id += 1
            
            # Add holiday or special events
            if current_date.day == 1 and current_date.month == 5:  # May 1
                events.append({
                    "event_id": f"event-{event_id}",
                    "calendar_name": cal_name,
                    "title": "Labor Day",
                    "location": "",
                    "description": "Public Holiday",
                    "start_date": current_date.strftime("%Y-%m-%d"),
                    "end_date": current_date.strftime("%Y-%m-%d"),
                    "all_day": True
                })
                event_id += 1
                
            current_date += timedelta(days=1)
        
        logger.info(f"Generated {len(events)} mock events for calendar '{cal_name}'")
        return events

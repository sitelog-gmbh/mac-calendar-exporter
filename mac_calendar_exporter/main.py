#!/usr/bin/env python3
"""
macOS Calendar Exporter Main Module.

This module is the main entry point for the macOS Calendar exporter application,
which exports calendar events to ICS files and uploads them to an SFTP server.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from mac_calendar_exporter.calendar.eventkit_calendar import EventKitCalendarAccess
from mac_calendar_exporter.calendar.mock_calendar import MockCalendarData  # Keeping mock data for fallback
from mac_calendar_exporter.ics.ics_generator import ICSGenerator
from mac_calendar_exporter.sftp.sftp_uploader import SFTPUploader
from mac_calendar_exporter.config.config_manager import ConfigManager


class MacCalendarExporter:
    """Main macOS Calendar exporter class that orchestrates the export process."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the CalDAV exporter.
        
        Args:
            config: Optional configuration dictionary to override defaults
        """
        # Set up logging
        self._setup_logging()
        
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Override with any provided config
        if config:
            self.config.update(config)
            
        self.logger = logging.getLogger(__name__)
        self.logger.info("macOS Calendar Exporter initialized")
        
    def _setup_logging(self):
        """Configure logging for the application."""
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            handlers=[logging.StreamHandler()]
        )
        
    def _get_calendar_accessor(self):
        """
        Get the calendar accessor using EventKit.
        
        Returns:
            An EventKitCalendarAccess instance
        """
        self.logger.info("Using Swift EventKit for calendar access")
        try:
            return EventKitCalendarAccess()
        except Exception as e:
            self.logger.error(f"Failed to initialize EventKit calendar accessor: {e}")
            return None

    def export_calendar(self):
        """
        Export calendar events to an ICS file.
        
        Returns:
            str: Path to the generated ICS file, or None if export failed
        """
        try:
            # Get calendar accessor
            calendar_accessor = self._get_calendar_accessor()
            
            # Get calendar configuration
            calendar_names = self.config.get('calendar_names', ['Calendar'])
            days_ahead = self.config.get('days_ahead', 30)
            days_behind = self.config.get('days_behind', 30)
            output_file = self.config.get('ics_file', './calendar_export.ics')
            
            # Calculate date range - now includes past events
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = today - timedelta(days=days_behind)
            end_date = today + timedelta(days=days_ahead)
            
            self.logger.info(f"Exporting events from {start_date.strftime('%Y-%m-%d')} to "
                           f"{end_date.strftime('%Y-%m-%d')} ({days_behind} days behind, {days_ahead} days ahead) "
                           f"for calendars: {', '.join(calendar_names)}")
            
            # Get events
            events = []
            if calendar_accessor is None:
                # Use mock data
                self.logger.info("Using mock calendar data")
                events = MockCalendarData.get_mock_events(
                    calendar_names=calendar_names,
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                # Get events from real calendar
                events = calendar_accessor.get_events(
                    calendar_names=calendar_names,
                    start_date=start_date,
                    end_date=end_date
                )
            
            self.logger.info(f"Retrieved {len(events)} events")
            
            # Generate ICS file
            if events:
                ics_generator = ICSGenerator()
                calendar_name = self.config.get('ics_calendar_name', 'Exported Calendar')
                include_details = self.config.get('include_details', False)
                title_length_limit = self.config.get('title_length_limit', 36)
                ics_file = ics_generator.generate_ics(
                    events=events,
                    calendar_name=calendar_name,
                    output_file=output_file,
                    include_details=include_details,
                    title_length_limit=title_length_limit
                )
                self.logger.info(f"Generated ICS file: {ics_file}")
                return ics_file
            else:
                self.logger.warning("No events found, skipping ICS generation")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to export calendar: {e}", exc_info=True)
            return None
            
    def upload_to_sftp(self, file_path: str):
        """
        Upload a file to an SFTP server.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            bool: True if upload succeeded, False otherwise
        """
        if not file_path or not os.path.exists(file_path):
            self.logger.error(f"File does not exist: {file_path}")
            return False
            
        try:
            # Get SFTP configuration
            sftp_config = self.config.get('sftp', {})
            if not sftp_config:
                self.logger.error("SFTP configuration not provided")
                return False
                
            hostname = sftp_config.get('host')  # The config uses 'host' but SFTPUploader expects 'hostname'
            port = sftp_config.get('port', 22)
            username = sftp_config.get('username')
            remote_path = sftp_config.get('remote_path', '/')
            
            if not hostname or not username:
                self.logger.error("SFTP host and username are required")
                return False
                
            # Get password or key file
            password = sftp_config.get('password')
            key_file = sftp_config.get('key_file')
            
            if not password and not key_file:
                self.logger.error("Either SFTP password or key file is required")
                return False
                
            # Upload file
            uploader = SFTPUploader(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                key_file=key_file
            )
            
            success = uploader.upload_file(file_path, remote_path)
            
            if success:
                self.logger.info(f"Successfully uploaded {file_path} to {hostname}:{remote_path}")
                return True
            else:
                self.logger.error(f"Failed to upload {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to upload to SFTP: {e}", exc_info=True)
            return False
    
    def import_to_local_calendar(self, file_path: str):
        """
        Import ICS file to a local/iCloud macOS calendar.
        
        Args:
            file_path: Path to the ICS file to import
            
        Returns:
            bool: True if import succeeded, False otherwise
        """
        if not file_path or not os.path.exists(file_path):
            self.logger.error(f"File does not exist: {file_path}")
            return False
        
        try:
            # Get local calendar name from config
            local_calendar = self.config.get('local_import_calendar', '')
            
            if not local_calendar:
                self.logger.error("Local import calendar name not configured")
                return False
            
            self.logger.info(f"Importing to local calendar: {local_calendar}")
            
            # Get calendar accessor
            calendar_accessor = self._get_calendar_accessor()
            
            if calendar_accessor is None:
                self.logger.error("Failed to initialize calendar accessor for local import")
                return False
            
            # Calculate date range for deletion (same as export range)
            days_ahead = self.config.get('days_ahead', 30)
            days_behind = self.config.get('days_behind', 30)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = today - timedelta(days=days_behind)
            end_date = today + timedelta(days=days_ahead)
            
            # First, delete existing events in the date range
            self.logger.info(f"Deleting existing events from {start_date.strftime('%Y-%m-%d')} "
                           f"to {end_date.strftime('%Y-%m-%d')}")
            delete_success = calendar_accessor.delete_calendar_events(
                calendar_name=local_calendar,
                start_date=start_date,
                end_date=end_date
            )
            
            if not delete_success:
                self.logger.warning("Failed to delete existing events, continuing with import anyway")
            
            # Import new events from ICS file
            self.logger.info(f"Importing events from {file_path}")
            import_success = calendar_accessor.import_ics_to_calendar(
                calendar_name=local_calendar,
                ics_file_path=file_path
            )
            
            if import_success:
                self.logger.info(f"Successfully imported events to calendar '{local_calendar}'")
                return True
            else:
                self.logger.error("Failed to import events to local calendar")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to import to local calendar: {e}", exc_info=True)
            return False
            
    def run(self):
        """
        Run the export and upload/import process.
        
        Returns:
            bool: True if the process succeeded, False otherwise
        """
        try:
            # Export calendar to ICS file
            ics_file = self.export_calendar()
            
            if not ics_file:
                self.logger.error("Calendar export failed")
                return False
            
            # Determine what to do with the exported file
            sftp_enabled = self.config.get('enable_sftp', False)
            local_import_calendar = self.config.get('local_import_calendar', '')
            
            # Check if SFTP is configured
            sftp_config = self.config.get('sftp', {})
            sftp_configured = bool(sftp_config.get('host') and sftp_config.get('username'))

            if local_import_calendar:
                # Import to local calendar
                self.logger.info(f"Importing to local calendar '{local_import_calendar}'")
                return self.import_to_local_calendar(ics_file)
            elif sftp_enabled and sftp_configured:
                # Upload ICS file to SFTP server
                self.logger.info("SFTP is configured and enabled, uploading file")
                return self.upload_to_sftp(ics_file)
            else:
                # Neither SFTP nor local import configured
                self.logger.info("Neither SFTP upload nor local import configured, file exported only")
                self.logger.info(f"Exported file available at: {ics_file}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to run export process: {e}", exc_info=True)
            return False


def main():
    """Run the macOS Calendar exporter from the command line."""
    parser = argparse.ArgumentParser(description="Export calendar events to ICS and upload to SFTP")
    parser.add_argument("--config", help="Path to custom config file")
    args = parser.parse_args()
    
    config = None
    if args.config:
        try:
            config_manager = ConfigManager(config_path=args.config)
            config = config_manager.get_config()
        except Exception as e:
            print(f"Error loading config file: {e}")
            return 1
    
    exporter = MacCalendarExporter(config=config)
    success = exporter.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

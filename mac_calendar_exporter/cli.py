#!/usr/bin/env python3
"""
macOS Calendar Exporter Command Line Interface.

This module provides a CLI for the macOS Calendar Exporter using the Click library.
"""

import logging
import os
import sys
from typing import List, Optional

import click

from mac_calendar_exporter.calendar.eventkit_calendar import EventKitCalendarAccess
from mac_calendar_exporter.config.config_manager import ConfigManager
from mac_calendar_exporter.main import MacCalendarExporter

# Set up logging
logger = logging.getLogger(__name__)


def setup_logging(level=logging.INFO):
    """Configure logging for the application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option(
    "--config", "-c", 
    type=click.Path(dir_okay=False),
    help="Path to config file"
)
@click.pass_context
def cli(ctx, debug, config):
    """
    macOS Calendar Exporter - Export calendar entries from macOS Calendar to ICS and upload to SFTP.
    
    This tool allows you to export calendar entries from the macOS Calendar app
    to an ICS file and optionally upload it to an SFTP server. This is useful for
    integrating with systems like Home Assistant that can read calendar data from
    ICS files but cannot directly access calendar services like iCloud or Google calendars.
    """
    # Set up logging
    log_level = logging.DEBUG if debug else logging.INFO
    setup_logging(log_level)
    
    # Initialize config
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["config_manager"] = ConfigManager(config)


@cli.command("export")
@click.option(
    "--calendar", "-cal",
    multiple=True,
    help="Calendar name(s) to export (can be used multiple times, empty means all calendars)"
)
@click.option(
    "--days", "-d",
    type=int,
    help="Number of days ahead to export"
)
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False),
    help="Output file path for ICS file"
)
@click.option(
    "--name", "-n",
    help="Name for the calendar in the ICS file"
)
@click.option(
    "--title-length", "-t",
    type=int,
    help="Maximum length for event titles (0 for unlimited, default: 32)"
)
@click.option(
    "--no-upload", is_flag=True,
    help="Skip uploading to SFTP server"
)
@click.pass_context
def export_calendar(ctx, calendar, days, output, name, title_length, no_upload):
    """Export calendar entries to ICS file and upload to SFTP server."""
    config_path = ctx.obj.get("config_path")
    
    # Convert tuple to list or None
    calendar_names = list(calendar) if calendar else None
    
    # Create exporter
    exporter = MacCalendarExporter(config=None)
    
    try:
        # Set up configuration
        if calendar_names:
            exporter.config['calendar_names'] = calendar_names
        if days:
            exporter.config['days_ahead'] = days
        if output:
            exporter.config['ics_file'] = output
        if name:
            exporter.config['ics_calendar_name'] = name
        if title_length is not None:
            exporter.config['title_length_limit'] = title_length
        if no_upload:
            exporter.config['enable_sftp'] = False
            
        # Run export
        success = exporter.run()
        ics_file = exporter.config.get('ics_file', './calendar_export.ics')
        
        click.echo(f"Export completed successfully. ICS file: {ics_file}")
    except Exception as e:
        logger.exception("Export failed")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command("list-calendars")
@click.pass_context
def list_calendars(ctx):
    """List available calendars in macOS Calendar app."""
    try:
        calendar_access = EventKitCalendarAccess()
        calendars = calendar_access.list_calendars()
        
        click.echo("Available calendars:")
        for cal in calendars:
            click.echo(f"  - {cal['title']}")
            
    except Exception as e:
        logger.exception("Failed to list calendars")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command("configure-sftp")
@click.option("--host", prompt="SFTP hostname")
@click.option("--port", prompt="SFTP port", default=22, type=int)
@click.option("--user", prompt="SFTP username")
@click.option(
    "--key-file",
    prompt="SSH key file path (leave empty for password auth)",
    default="",
    show_default=False
)
@click.option(
    "--remote-path",
    prompt="Remote file path",
    default="/calendar/calendar.ics"
)
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="SFTP password (not required if using key-based auth with no passphrase)"
)
@click.pass_context
def configure_sftp(ctx, host, port, user, key_file, remote_path, password):
    """Configure SFTP connection settings."""
    config_manager = ctx.obj.get("config_manager")
    
    # Update configuration
    config_manager.config["sftp"]["hostname"] = host
    config_manager.config["sftp"]["port"] = port
    config_manager.config["sftp"]["username"] = user
    
    if key_file:
        config_manager.config["sftp"]["key_file"] = os.path.expanduser(key_file)
        
    config_manager.config["sftp"]["remote_path"] = remote_path
    
    # Save configuration
    result = config_manager.save_config()
    
    # Store password securely if provided
    if password:
        pw_result = config_manager.set_sftp_password(password)
        if not pw_result:
            click.echo("Failed to store SFTP password securely.", err=True)
    
    if result:
        click.echo("SFTP configuration saved successfully.")
    else:
        click.echo("Failed to save SFTP configuration.", err=True)
        sys.exit(1)


@cli.command("configure-calendar")
@click.option(
    "--calendar", "-cal",
    multiple=True,
    help="Calendar name(s) to export (can be used multiple times, empty means all calendars)"
)
@click.option(
    "--days", "-d",
    type=int,
    prompt="Number of days ahead to export",
    default=30
)
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False),
    prompt="Output file path",
    default=os.path.expanduser("~/calendar_export.ics")
)
@click.option(
    "--name", "-n",
    prompt="Calendar name in ICS file",
    default="Exported Calendar"
)
@click.option(
    "--title-length", "-t",
    type=int,
    prompt="Maximum length for event titles (0 for unlimited)",
    default=32
)
@click.pass_context
def configure_calendar(ctx, calendar, days, output, name, title_length):
    """Configure calendar export settings."""
    config_manager = ctx.obj.get("config_manager")
    
    # Update configuration
    config_manager.config["calendar"]["names"] = list(calendar)
    config_manager.config["calendar"]["days_ahead"] = days
    config_manager.config["calendar"]["output_file"] = os.path.expanduser(output)
    config_manager.config["calendar"]["output_name"] = name
    config_manager.config["calendar"]["title_length_limit"] = title_length
    
    # Save configuration
    result = config_manager.save_config()
    
    if result:
        click.echo("Calendar configuration saved successfully.")
        
        if not calendar:
            click.echo("Note: No specific calendars selected - all calendars will be exported.")
    else:
        click.echo("Failed to save calendar configuration.", err=True)
        sys.exit(1)


@cli.command("configure-schedule")
@click.option(
    "--enabled/--disabled",
    prompt="Enable scheduled exports",
    default=True
)
@click.option(
    "--interval",
    type=click.Choice(["hourly", "daily"]),
    prompt="Export interval",
    default="daily"
)
@click.option(
    "--time",
    prompt="Time for daily export (HH:MM)",
    default="04:00",
    help="Time for daily exports in 24h format (HH:MM)"
)
@click.pass_context
def configure_schedule(ctx, enabled, interval, time):
    """Configure scheduled exports."""
    config_manager = ctx.obj.get("config_manager")
    
    # Validate time format for daily exports
    if interval == "daily":
        try:
            hour, minute = time.split(":")
            hour = int(hour)
            minute = int(minute)
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError()
        except:
            click.echo("Invalid time format. Please use HH:MM in 24h format.", err=True)
            sys.exit(1)
    
    # Update configuration
    config_manager.config["schedule"]["enabled"] = enabled
    config_manager.config["schedule"]["interval"] = interval
    config_manager.config["schedule"]["time"] = time
    
    # Save configuration
    result = config_manager.save_config()
    
    if result:
        click.echo("Schedule configuration saved successfully.")
        
        if enabled:
            if interval == "daily":
                click.echo(f"Exports will run daily at {time}.")
            else:
                click.echo("Exports will run hourly.")
                
            # Note about actually setting up the schedule
            click.echo("\nIMPORTANT: This only saves the schedule configuration.")
            click.echo("To actually schedule the export, you need to set up:")
            click.echo(" - For macOS: A launchd plist file (see documentation)")
            click.echo(" - For manual scheduling: A cron job or other scheduler")
    else:
        click.echo("Failed to save schedule configuration.", err=True)
        sys.exit(1)


@cli.command("show-config")
@click.pass_context
def show_config(ctx):
    """Show current configuration."""
    import json
    
    config_manager = ctx.obj.get("config_manager")
    config = config_manager._get_saveable_config()  # Get config without sensitive data
    
    click.echo(json.dumps(config, indent=2))


def main():
    """Main entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()

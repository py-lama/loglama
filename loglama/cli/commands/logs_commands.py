#!/usr/bin/env python3
"""
Log management commands for the LogLama CLI.

This module contains commands for viewing, filtering, and managing log records.
"""

import json
import sys

import click

# Try to import rich for enhanced console output
try:
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from loglama.cli.utils import get_console
from loglama.config.env_loader import get_env
from loglama.core.logger import get_logger

# Import log collector
try:
    from loglama.collectors.log_collector import (
        collect_all_logs,
        collect_logs_from_component,
    )
    from loglama.collectors.scheduled_collector import run_collector

    COLLECTOR_AVAILABLE = True
except ImportError:
    COLLECTOR_AVAILABLE = False

# Get console instance
console = get_console()


@click.command()
@click.option(
    "--level", default=None, help="Filter by log level (e.g., INFO, ERROR)"
)
@click.option(
    "--logger-name", "--logger", default=None, help="Filter by logger name"
)
@click.option("--module", default=None, help="Filter by module name")
@click.option("--limit", default=50, help="Maximum number of logs to display")
@click.option(
    "--json-output/--no-json-output",
    "--json/--no-json",
    default=False,
    help="Output in JSON format",
)
def logs(level, logger_name, module, limit, json_output):
    """Display log records from the database."""
    # Initialize CLI logger
    logger = get_logger("loglama.cli")

    try:
        # Import database modules
        try:
            from loglama.db.models import LogRecord, create_tables, get_session
        except ImportError:
            console.print(
                "[red]Database module not available. Install loglama[db] for database support.[/red]"
            )
            sys.exit(1)

        # Ensure tables exist
        create_tables()

        # Create session and query
        session = get_session()
        query = session.query(LogRecord)

        # Apply filters
        if level:
            query = query.filter(LogRecord.level == level.upper())
        if logger_name:
            query = query.filter(
                LogRecord.logger_name.like(f"%{logger_name}%")
            )
        if module:
            query = query.filter(LogRecord.module.like(f"%{module}%"))

        # Apply limit and ordering
        query = query.order_by(LogRecord.timestamp.desc()).limit(limit)

        # Execute query
        log_records = query.all()

        # Close session
        session.close()

        if json_output:
            # Output in JSON format
            results = [record.to_dict() for record in log_records]
            click.echo(json.dumps(results, indent=2, default=str))
        else:
            # Output in table format
            if RICH_AVAILABLE:
                table = Table(title="Log Records")
                table.add_column("ID", justify="right")
                table.add_column("Timestamp")
                table.add_column("Level")
                table.add_column("Logger")
                table.add_column("Message")

                for record in log_records:
                    level_style = {
                        "DEBUG": "dim",
                        "INFO": "green",
                        "WARNING": "yellow",
                        "ERROR": "red",
                        "CRITICAL": "bold red",
                    }.get(record.level, "")

                    table.add_row(
                        str(record.id),
                        record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        f"[{level_style}]{record.level}[/{level_style}]",
                        record.logger_name,
                        record.message[:100]
                        + ("..." if len(record.message) > 100 else ""),
                    )

                console.print(table)
            else:
                # Fallback to simple table
                click.echo(
                    f"{'ID':>5} | {'Timestamp':<19} | {'Level':<8} | {'Logger':<20} | Message"
                )
                click.echo("-" * 80)

                for record in log_records:
                    click.echo(
                        f"{record.id:>5} | "
                        f"{record.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<19} | "
                        f"{record.level:<8} | "
                        f"{record.logger_name[:20]:<20} | "
                        f"{record.message[:100] + ('...' if len(record.message) > 100 else '')}"
                    )
    except Exception as e:
        logger.exception(f"Error displaying logs: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@click.command()
@click.argument("log_id", type=int)
def view(log_id):
    """View details of a specific log record."""
    try:
        # Import database modules
        try:
            from loglama.db.models import LogRecord, get_session
        except ImportError:
            console.print(
                "[red]Database module not available. Install loglama[db] for database support.[/red]"
            )
            sys.exit(1)

        # Create session and query
        session = get_session()
        record = (
            session.query(LogRecord).filter(LogRecord.id == log_id).first()
        )

        # Close session
        session.close()

        if not record:
            console.print(f"[red]Log record with ID {log_id} not found.[/red]")
            sys.exit(1)

        # Output in rich format if available
        if RICH_AVAILABLE:
            from rich.panel import Panel
            from rich.syntax import Syntax

            # Format timestamp
            timestamp = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")

            # Format level with color
            level_style = {
                "DEBUG": "dim",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold red",
            }.get(record.level, "")

            # Format context if available
            context = None
            if record.context:
                try:
                    context_data = json.loads(record.context)
                    context = json.dumps(context_data, indent=2)
                except (json.JSONDecodeError, TypeError):
                    context = record.context

            # Format exception info if available
            exception_info = (
                record.exception_info if record.exception_info else None
            )

            # Create panel with log record details
            content = f"""[bold]ID:[/bold] {record.id}
[bold]Timestamp:[/bold] {timestamp}
[bold]Level:[/bold] [{level_style}]{record.level}[/{level_style}]
[bold]Logger:[/bold] {record.logger_name}
[bold]Module:[/bold] {record.module}
[bold]Function:[/bold] {record.function}
[bold]Line:[/bold] {record.line_number}
[bold]Process:[/bold] {record.process_id} ({record.process_name})
[bold]Thread:[/bold] {record.thread_id} ({record.thread_name})

[bold]Message:[/bold]
{record.message}"""

            panel = Panel(
                content, title=f"Log Record #{record.id}", expand=False
            )
            console.print(panel)

            # Print context if available
            if context:
                console.print("[bold]Context:[/bold]")
                syntax = Syntax(
                    context, "json", theme="monokai", line_numbers=True
                )
                console.print(syntax)

            # Print exception info if available
            if exception_info:
                console.print("[bold]Exception:[/bold]")
                console.print(exception_info)
        else:
            # Fallback to simple output
            click.echo(f"Log Record #{record.id}")
            click.echo("-" * 40)
            click.echo(
                f"Timestamp: {record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            click.echo(f"Level: {record.level}")
            click.echo(f"Logger: {record.logger_name}")
            click.echo(f"Module: {record.module}")
            click.echo(f"Function: {record.function}")
            click.echo(f"Line: {record.line_number}")
            click.echo(f"Process: {record.process_id} ({record.process_name})")
            click.echo(f"Thread: {record.thread_id} ({record.thread_name})")
            click.echo("")
            click.echo("Message:")
            click.echo(record.message)

            # Print context if available
            if record.context:
                click.echo("")
                click.echo("Context:")
                try:
                    context_data = json.loads(record.context)
                    click.echo(json.dumps(context_data, indent=2))
                except (json.JSONDecodeError, TypeError):
                    click.echo(record.context)

            # Print exception info if available
            if record.exception_info:
                click.echo("")
                click.echo("Exception:")
                click.echo(record.exception_info)
    except Exception as e:
        console.print(f"[red]Error viewing log record: {str(e)}[/red]")
        sys.exit(1)


@click.command()
@click.option(
    "--level", default=None, help="Filter by log level (e.g., INFO, ERROR)"
)
@click.option(
    "--logger-name", "--logger", default=None, help="Filter by logger name"
)
@click.option("--module", default=None, help="Filter by module name")
@click.option(
    "--all", is_flag=True, help="Clear all logs (ignores other filters)"
)
@click.confirmation_option(prompt="Are you sure you want to clear these logs?")
def clear(level, logger_name, module, all):
    """Clear log records from the database."""
    try:
        # Import database modules
        try:
            from loglama.db.models import LogRecord, create_tables, get_session
        except ImportError:
            console.print(
                "[red]Database module not available. Install loglama[db] for database support.[/red]"
            )
            sys.exit(1)

        # Ensure tables exist
        create_tables()

        # Create session and query
        session = get_session()
        query = session.query(LogRecord)

        # Apply filters if not clearing all
        if not all:
            if level:
                query = query.filter(LogRecord.level == level.upper())
            if logger_name:
                query = query.filter(
                    LogRecord.logger_name.like(f"%{logger_name}%")
                )
            if module:
                query = query.filter(LogRecord.module.like(f"%{module}%"))

        # Get count before deletion
        count = query.count()

        # Delete matching records
        query.delete()
        session.commit()

        # Close session
        session.close()

        # Print success message
        console.print(
            f"[green]Successfully cleared {count} log records.[/green]"
        )
    except Exception as e:
        console.print(f"[red]Error clearing logs: {str(e)}[/red]")
        sys.exit(1)


@click.command()
def stats():
    """Show statistics about log records."""
    try:
        # Import database modules
        try:
            from sqlalchemy import func

            from loglama.db.models import LogRecord, create_tables, get_session
        except ImportError:
            console.print(
                "[red]Database module not available. Install loglama[db] for database support.[/red]"
            )
            sys.exit(1)

        # Ensure tables exist
        create_tables()

        # Create session
        session = get_session()

        # Get total count
        total_count = session.query(func.count(LogRecord.id)).scalar()

        # Get counts by level
        level_counts = (
            session.query(
                LogRecord.level, func.count(LogRecord.id).label("count")
            )
            .group_by(LogRecord.level)
            .all()
        )

        # Get counts by logger
        logger_counts = (
            session.query(
                LogRecord.logger_name, func.count(LogRecord.id).label("count")
            )
            .group_by(LogRecord.logger_name)
            .all()
        )

        # Get counts by module
        module_counts = (
            session.query(
                LogRecord.module, func.count(LogRecord.id).label("count")
            )
            .group_by(LogRecord.module)
            .all()
        )

        # Get oldest and newest records
        oldest_record = (
            session.query(LogRecord)
            .order_by(LogRecord.timestamp.asc())
            .first()
        )
        newest_record = (
            session.query(LogRecord)
            .order_by(LogRecord.timestamp.desc())
            .first()
        )

        # Close session
        session.close()

        # Output statistics
        if RICH_AVAILABLE:
            from rich.panel import Panel

            # Format date range
            date_range = "N/A"
            if oldest_record and newest_record:
                oldest_date = oldest_record.timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                newest_date = newest_record.timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                date_range = f"{oldest_date} to {newest_date}"

            # Create summary panel
            summary = f"""[bold]Total Records:[/bold] {total_count}
[bold]Date Range:[/bold] {date_range}"""
            summary_panel = Panel(
                summary, title="Log Statistics Summary", expand=False
            )
            console.print(summary_panel)

            # Create level counts table
            level_table = Table(title="Records by Level")
            level_table.add_column("Level", style="bold")
            level_table.add_column("Count", justify="right")
            level_table.add_column("Percentage", justify="right")

            for level, count in level_counts:
                percentage = (
                    (count / total_count) * 100 if total_count > 0 else 0
                )
                level_style = {
                    "DEBUG": "dim",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold red",
                }.get(level, "")

                level_table.add_row(
                    f"[{level_style}]{level}[/{level_style}]",
                    str(count),
                    f"{percentage:.2f}%",
                )

            console.print(level_table)

            # Create logger counts table
            logger_table = Table(title="Top Loggers")
            logger_table.add_column("Logger", style="bold")
            logger_table.add_column("Count", justify="right")
            logger_table.add_column("Percentage", justify="right")

            for logger_name, count in sorted(
                logger_counts, key=lambda x: x[1], reverse=True
            )[:10]:
                percentage = (
                    (count / total_count) * 100 if total_count > 0 else 0
                )
                logger_table.add_row(
                    logger_name, str(count), f"{percentage:.2f}%"
                )

            console.print(logger_table)

            # Create module counts table
            module_table = Table(title="Top Modules")
            module_table.add_column("Module", style="bold")
            module_table.add_column("Count", justify="right")
            module_table.add_column("Percentage", justify="right")

            for module, count in sorted(
                module_counts, key=lambda x: x[1], reverse=True
            )[:10]:
                percentage = (
                    (count / total_count) * 100 if total_count > 0 else 0
                )
                module_table.add_row(
                    module or "<None>", str(count), f"{percentage:.2f}%"
                )

            console.print(module_table)
        else:
            # Fallback to simple output
            click.echo("Log Statistics Summary")
            click.echo("-" * 40)
            click.echo(f"Total Records: {total_count}")

            # Format date range
            if oldest_record and newest_record:
                oldest_date = oldest_record.timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                newest_date = newest_record.timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                click.echo(f"Date Range: {oldest_date} to {newest_date}")
            else:
                click.echo("Date Range: N/A")

            # Print level counts
            click.echo("\nRecords by Level:")
            click.echo("-" * 40)
            for level, count in level_counts:
                percentage = (
                    (count / total_count) * 100 if total_count > 0 else 0
                )
                click.echo(f"{level:<10} {count:>10} {percentage:.2f}%")

            # Print top loggers
            click.echo("\nTop Loggers:")
            click.echo("-" * 40)
            for logger_name, count in sorted(
                logger_counts, key=lambda x: x[1], reverse=True
            )[:10]:
                percentage = (
                    (count / total_count) * 100 if total_count > 0 else 0
                )
                click.echo(f"{logger_name:<30} {count:>10} {percentage:.2f}%")

            # Print top modules
            click.echo("\nTop Modules:")
            click.echo("-" * 40)
            for module, count in sorted(
                module_counts, key=lambda x: x[1], reverse=True
            )[:10]:
                percentage = (
                    (count / total_count) * 100 if total_count > 0 else 0
                )
                module_name = module or "<None>"
                click.echo(f"{module_name:<30} {count:>10} {percentage:.2f}%")
    except Exception as e:
        console.print(f"[red]Error showing statistics: {str(e)}[/red]")
        sys.exit(1)


@click.command()
@click.option(
    "--component",
    help="Specific component to collect logs from (e.g., weblama, apilama)",
)
@click.option("--all", is_flag=True, help="Collect logs from all components")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed import information"
)
def collect(component, all, verbose):
    """Collect logs from other PyLama components and import them into LogLama.

    This command imports logs from WebLama, APILama, BEXY, PyLLM, and other
    PyLama components into the central LogLama database.
    """
    # Initialize CLI logger
    logger = get_logger("loglama.cli")

    if not COLLECTOR_AVAILABLE:
        console.print(
            "[red]Log collector module not available. Please check your installation.[/red]"
        )
        sys.exit(1)

    try:
        # Ensure database tables exist
        from loglama.db.models import create_tables

        create_tables()

        if all:
            # Collect logs from all components
            console.print("Collecting logs from all PyLama components...")
            results = collect_all_logs()

            # Print results
            total_count = sum(results.values())

            if RICH_AVAILABLE:
                from rich.table import Table

                table = Table(title="Log Collection Results")
                table.add_column("Component")
                table.add_column("Records Imported", justify="right")

                for component_name, count in results.items():
                    table.add_row(component_name, str(count))

                table.add_row("Total", str(total_count), style="bold")
                console.print(table)
            else:
                console.print(
                    f"Imported {total_count} log records from all components:"
                )
                for component_name, count in results.items():
                    console.print(f"  {component_name}: {count} records")

        elif component:
            # Collect logs from a specific component
            console.print(f"Collecting logs from {component}...")
            count = collect_logs_from_component(component)

            if count > 0:
                console.print(
                    f"[green]Successfully imported {count} log records from {component}[/green]"
                )
            else:
                console.print(
                    f"[yellow]No log records found for {component}[/yellow]"
                )

        else:
            console.print(
                "[yellow]Please specify a component with --component or use --all to collect from all components[/yellow]"  # noqa: E501
            )
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Error collecting logs: {str(e)}")
        console.print(f"[red]Error collecting logs: {str(e)}[/red]")
        sys.exit(1)


@click.command()
@click.option(
    "--components",
    "-c",
    multiple=True,
    help="Components to collect logs from (default: all)",
)
@click.option(
    "--interval",
    "-i",
    type=int,
    default=300,
    help="Collection interval in seconds (default: 300)",
)
@click.option(
    "--once", "-o", is_flag=True, help="Run only once instead of periodically"
)
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
@click.option(
    "--background",
    "-b",
    is_flag=True,
    help="Run in the background (daemon mode)",
)
def collect_daemon(components, interval, once, verbose, background):
    """Run the scheduled log collector as a daemon.

    This command starts a background process that periodically collects logs from
    WebLama, APILama, and other PyLama components and imports them into the
    central LogLama database.
    """
    # Initialize CLI logger
    logger = get_logger("loglama.cli")

    if not COLLECTOR_AVAILABLE:
        console.print(
            "[red]Log collector module not available. Please check your installation.[/red]"
        )
        sys.exit(1)

    try:
        # Convert components to list
        component_list = list(components) if components else None

        if background:
            # Run in the background
            import subprocess
            from pathlib import Path

            # Create the command
            cmd = [
                sys.executable,
                "-m",
                "loglama.collectors.scheduled_collector",
            ]

            # Add arguments
            if component_list:
                cmd.extend(["--components"] + component_list)
            if interval != 300:
                cmd.extend(["--interval", str(interval)])
            if once:
                cmd.append("--once")
            if verbose:
                cmd.append("--verbose")

            # Create log directory if it doesn't exist
            log_dir = Path(get_env("LOGLAMA_LOG_DIR", "logs"))
            log_dir.mkdir(exist_ok=True)

            # Open log file
            log_file = open(log_dir / "collector.log", "a")

            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=log_file,
                close_fds=True,
                start_new_session=True,
            )

            # Print success message
            console.print(
                f"[green]Started log collector daemon with PID {process.pid}[/green]"
            )
            console.print(
                f"Logs are being written to {log_dir / 'collector.log'}"
            )

            # Write PID to file for later management
            with open(log_dir / "collector.pid", "w") as f:
                f.write(str(process.pid))
        else:
            # Run in the foreground
            console.print(
                f"Starting log collector for {', '.join(component_list) if component_list else 'all components'}"
            )
            console.print(f"Collection interval: {interval} seconds")
            console.print("Press Ctrl+C to stop")

            # Run the collector
            run_collector(
                components=component_list,
                interval=interval,
                once=once,
                verbose=verbose,
            )

    except KeyboardInterrupt:
        console.print("[yellow]Log collector stopped by user[/yellow]")

    except Exception as e:
        logger.exception(f"Error starting log collector: {str(e)}")
        console.print(f"[red]Error starting log collector: {str(e)}[/red]")
        sys.exit(1)

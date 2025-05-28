#!/usr/bin/env python3
"""
Environment management commands for the LogLama CLI.

This module contains commands for managing the centralized environment
for the PyLama ecosystem.
"""

import os
import sys
from pathlib import Path

import click

# Try to import rich for enhanced console output
try:
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from loglama.cli.utils import get_console
from loglama.core.env_manager import (
    ensure_required_env_vars,
    get_central_env_path,
    load_central_env,
)
from loglama.core.logger import get_logger

# Get console instance
console = get_console()


@click.command()
@click.option(
    "--env-file", default=None, help="Path to .env file to initialize from"
)
@click.option(
    "--verbose/--no-verbose", default=True, help="Show verbose output"
)
@click.option(
    "--force/--no-force",
    default=False,
    help="Force overwrite of existing .env file",
)
def init(env_file, verbose, force):
    """Initialize LogLama configuration and the centralized environment."""
    # Initialize CLI logger
    logger = get_logger("loglama.cli")

    try:
        # Get the central .env path
        central_env_path = get_central_env_path()

        if verbose:
            console.print(
                f"Initializing LogLama environment at {central_env_path}"
            )

        # Check if central .env file already exists
        if central_env_path.exists() and not force:
            console.print(
                f"[yellow]Central .env file already exists at {central_env_path}[/yellow]"
            )
            console.print("Use --force to overwrite the existing file.")
            return

        # Create the directory if it doesn't exist
        central_env_path.parent.mkdir(parents=True, exist_ok=True)

        # If a custom .env file is provided, copy it to the central location
        if env_file:
            env_file_path = Path(env_file)
            if not env_file_path.exists():
                console.print(
                    f"[red]Error: .env file not found at {env_file_path}[/red]"
                )
                sys.exit(1)

            # Copy the file
            with open(env_file_path, "r") as src, open(
                central_env_path, "w"
            ) as dst:
                dst.write(src.read())

            if verbose:
                console.print(
                    f"[green]Copied {env_file_path} to {central_env_path}[/green]"
                )
        else:
            # Create a default .env file
            default_env = {
                "LOGLAMA_LEVEL": "INFO",
                "LOGLAMA_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "LOGLAMA_DATE_FORMAT": "%Y-%m-%d %H:%M:%S",
                "LOGLAMA_DIR": "logs",
                "LOGLAMA_DB_PATH": str(
                    Path.home() / ".loglama" / "loglama.db"
                ),
                "OLLAMA_MODEL": "llama3",
                "OLLAMA_FALLBACK_MODELS": "mistral,llama2",
                "OLLAMA_PATH": "/usr/local/bin/ollama",
                "MODELS_DIR": "./models",
                "DEVLAMA_DEBUG": "false",
            }

            # Write the default .env file
            with open(central_env_path, "w") as f:
                for key, value in default_env.items():
                    f.write(f"{key}={value}\n")

            if verbose:
                console.print(
                    f"[green]Created default .env file at {central_env_path}[/green]"
                )

        # Load the central .env file
        load_central_env()

        # Ensure required environment variables are set
        ensure_required_env_vars()

        if verbose:
            console.print(
                "[green]LogLama environment initialized successfully[/green]"
            )
    except Exception as e:
        logger.exception(f"Error initializing environment: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@click.command()
@click.option(
    "--verbose/--no-verbose",
    default=False,
    help="Show all environment variables, including empty ones",
)
def env(verbose):
    """Show the current environment variables."""
    try:
        # Load the central .env file
        load_central_env()

        # Get the central .env path
        central_env_path = get_central_env_path()

        # Check if the central .env file exists
        if not central_env_path.exists():
            console.print(
                f"[yellow]Central .env file not found at {central_env_path}[/yellow]"
            )
            console.print("Run 'loglama init' to create it.")
            return

        # Read the .env file
        env_vars = {}
        with open(central_env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

        # Get environment variables from the OS environment
        os_env_vars = {}
        for key, value in os.environ.items():
            if key.startswith(("LOGLAMA_", "OLLAMA_", "DEVLAMA_", "MODELS_")):
                os_env_vars[key] = value

        # Output in table format
        if RICH_AVAILABLE:
            # Create a table for .env file variables
            env_table = Table(
                title=f"Environment Variables from {central_env_path}"
            )
            env_table.add_column("Variable", style="bold")
            env_table.add_column("Value")
            env_table.add_column("Source")

            # Add rows for .env file variables
            for key, value in sorted(env_vars.items()):
                # Skip empty values if not verbose
                if not value and not verbose:
                    continue

                # Check if the variable is overridden in the OS environment
                source = "[green].env file[/green]"
                if key in os_env_vars and os_env_vars[key] != value:
                    value = os_env_vars[key]
                    source = "[yellow]OS environment (overridden)[/yellow]"

                env_table.add_row(key, value, source)

            # Add rows for OS environment variables not in .env file
            for key, value in sorted(os_env_vars.items()):
                if key not in env_vars:
                    # Skip empty values if not verbose
                    if not value and not verbose:
                        continue

                    env_table.add_row(
                        key, value, "[blue]OS environment[/blue]"
                    )

            console.print(env_table)
        else:
            # Fallback to simple output
            click.echo(f"Environment Variables from {central_env_path}:")
            click.echo("-" * 80)
            click.echo(f"{'Variable':<30} {'Value':<40} {'Source':<20}")
            click.echo("-" * 80)

            # Print .env file variables
            for key, value in sorted(env_vars.items()):
                # Skip empty values if not verbose
                if not value and not verbose:
                    continue

                # Check if the variable is overridden in the OS environment
                source = ".env file"
                if key in os_env_vars and os_env_vars[key] != value:
                    value = os_env_vars[key]
                    source = "OS environment (overridden)"

                click.echo(f"{key:<30} {value:<40} {source:<20}")

            # Print OS environment variables not in .env file
            for key, value in sorted(os_env_vars.items()):
                if key not in env_vars:
                    # Skip empty values if not verbose
                    if not value and not verbose:
                        continue

                    click.echo(f"{key:<30} {value:<40} {'OS environment':<20}")
    except Exception as e:
        console.print(
            f"[red]Error showing environment variables: {str(e)}[/red]"
        )
        sys.exit(1)

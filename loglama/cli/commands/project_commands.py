#!/usr/bin/env python3
"""
Project management commands for the LogLama CLI.

This module contains commands for managing PyLama ecosystem projects,
including dependency checking, testing, and starting services.
"""

import sys

import click

from loglama.cli.utils import get_console
from loglama.core.env_manager import (
    check_project_dependencies,
    ensure_required_env_vars,
    install_project_dependencies,
    load_central_env,
    run_project_tests,
    start_project,
)
from loglama.core.logger import get_logger

# Get console instance
console = get_console()


@click.command()
@click.argument(
    "project",
    type=click.Choice(["loglama", "pylama", "pyllm", "bexy", "weblama"]),
)
@click.option(
    "--install/--no-install",
    default=False,
    help="Install missing dependencies",
)
@click.option(
    "--verbose/--no-verbose", default=True, help="Show verbose output"
)
def check_deps(project, install, verbose):
    """Check and optionally install dependencies for a project."""
    # Initialize CLI logger
    logger = get_logger("loglama.cli")

    try:
        # Load the central .env file
        load_central_env()

        # Check dependencies
        missing_deps = check_project_dependencies(project, verbose=verbose)

        if not missing_deps:
            console.print(
                f"[green]All dependencies for {project} are satisfied.[/green]"
            )
            return

        # Install dependencies if requested
        if install:
            console.print(f"Installing missing dependencies for {project}...")
            install_project_dependencies(
                project, missing_deps, verbose=verbose
            )
            console.print(
                f"[green]Dependencies for {project} installed successfully.[/green]"
            )
        else:
            console.print(
                f"[yellow]Missing dependencies for {project}:[/yellow]"
            )
            for dep in missing_deps:
                console.print(f"  - {dep}")
            console.print(
                "\nRun with --install to install missing dependencies."
            )
    except Exception as e:
        logger.exception(f"Error checking dependencies: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@click.command()
@click.argument(
    "project",
    type=click.Choice(["loglama", "pylama", "pyllm", "bexy", "weblama"]),
)
@click.option(
    "--verbose/--no-verbose", default=True, help="Show verbose output"
)
def test(project, verbose):
    """Run tests for a project."""
    # Initialize CLI logger
    logger = get_logger("loglama.cli")

    try:
        # Load the central .env file
        load_central_env()

        # Run tests
        console.print(f"Running tests for {project}...")
        success = run_project_tests(project, verbose=verbose)

        if success:
            console.print(
                f"[green]Tests for {project} passed successfully.[/green]"
            )
        else:
            console.print(f"[red]Tests for {project} failed.[/red]")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Error running tests: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@click.command()
@click.argument(
    "project",
    type=click.Choice(["loglama", "pylama", "pyllm", "bexy", "weblama"]),
)
@click.option(
    "--check-deps/--no-check-deps",
    default=True,
    help="Check dependencies before starting",
)
@click.option(
    "--install-deps/--no-install-deps",
    default=False,
    help="Install missing dependencies",
)
@click.option(
    "--verbose/--no-verbose", default=True, help="Show verbose output"
)
@click.argument("args", nargs=-1)
def start(project, check_deps, install_deps, verbose, args):
    """Start a project with the centralized environment."""
    # Initialize CLI logger
    logger = get_logger("loglama.cli")

    try:
        # Load the central .env file
        load_central_env()

        # Ensure required environment variables are set
        ensure_required_env_vars()

        # Check dependencies if requested
        if check_deps:
            missing_deps = check_project_dependencies(project, verbose=verbose)

            if missing_deps:
                if install_deps:
                    console.print(
                        f"Installing missing dependencies for {project}..."
                    )
                    install_project_dependencies(
                        project, missing_deps, verbose=verbose
                    )
                    console.print(
                        f"[green]Dependencies for {project} installed successfully.[/green]"
                    )
                else:
                    console.print(
                        f"[yellow]Missing dependencies for {project}:[/yellow]"
                    )
                    for dep in missing_deps:
                        console.print(f"  - {dep}")
                    console.print(
                        "\nRun with --install-deps to install missing dependencies."
                    )
                    sys.exit(1)

        # Start the project
        console.print(f"Starting {project}...")
        start_project(project, args, verbose=verbose)
    except Exception as e:
        logger.exception(f"Error starting project: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@click.command()
@click.option(
    "--check-deps/--no-check-deps",
    default=True,
    help="Check dependencies before starting",
)
@click.option(
    "--install-deps/--no-install-deps",
    default=False,
    help="Install missing dependencies",
)
@click.option(
    "--verbose/--no-verbose", default=True, help="Show verbose output"
)
@click.option("--loglama/--no-loglama", default=True, help="Start LogLama")
@click.option("--pylama/--no-pylama", default=True, help="Start PyLama")
@click.option("--pyllm/--no-pyllm", default=True, help="Start PyLLM")
@click.option("--bexy/--no-bexy", default=True, help="Start BEXY")
@click.option("--weblama/--no-weblama", default=True, help="Start WebLama")
def start_all(
    check_deps, install_deps, verbose, loglama, pylama, pyllm, bexy, weblama
):
    """Start all PyLama ecosystem services."""
    # Initialize CLI logger
    logger = get_logger("loglama.cli")

    try:
        # Load the central .env file
        load_central_env()

        # Ensure required environment variables are set
        ensure_required_env_vars()

        # Define the order of services to start
        services = []
        if loglama:
            services.append("loglama")
        if pylama:
            services.append("pylama")
        if pyllm:
            services.append("pyllm")
        if bexy:
            services.append("bexy")
        if weblama:
            services.append("weblama")

        if not services:
            console.print("[yellow]No services selected to start.[/yellow]")
            return

        # Check dependencies for all services if requested
        if check_deps:
            all_missing_deps = {}
            for service in services:
                missing_deps = check_project_dependencies(
                    service, verbose=verbose
                )
                if missing_deps:
                    all_missing_deps[service] = missing_deps

            if all_missing_deps:
                if install_deps:
                    for service, missing_deps in all_missing_deps.items():
                        console.print(
                            f"Installing missing dependencies for {service}..."
                        )
                        install_project_dependencies(
                            service, missing_deps, verbose=verbose
                        )
                        console.print(
                            f"[green]Dependencies for {service} installed successfully.[/green]"
                        )
                else:
                    console.print("[yellow]Missing dependencies:[/yellow]")
                    for service, missing_deps in all_missing_deps.items():
                        console.print(f"\n{service}:")
                        for dep in missing_deps:
                            console.print(f"  - {dep}")
                    console.print(
                        "\nRun with --install-deps to install missing dependencies."
                    )
                    sys.exit(1)

        # Start each service
        processes = {}
        for service in services:
            console.print(f"Starting {service}...")
            try:
                # Start the service in a separate process
                process = start_project(
                    service, [], verbose=verbose, background=True
                )
                if process:
                    processes[service] = process
                    console.print(
                        f"[green]{service} started successfully (PID: {process.pid})[/green]"
                    )
                else:
                    console.print(
                        f"[yellow]Failed to start {service} in background mode.[/yellow]"
                    )
            except Exception as e:
                console.print(f"[red]Error starting {service}: {str(e)}[/red]")

        # Print summary
        if processes:
            console.print("\n[green]Services started:[/green]")
            for service, process in processes.items():
                console.print(f"  - {service} (PID: {process.pid})")

            console.print("\nPress Ctrl+C to stop all services.")

            # Wait for user to press Ctrl+C
            try:
                for process in processes.values():
                    process.wait()
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping all services...[/yellow]")
                for service, process in processes.items():
                    try:
                        process.terminate()
                        console.print(f"[green]{service} stopped.[/green]")
                    except Exception as e:
                        console.print(
                            f"[red]Error stopping {service}: {str(e)}[/red]"
                        )
        else:
            console.print("[yellow]No services were started.[/yellow]")
    except Exception as e:
        logger.exception(f"Error starting services: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

#!/usr/bin/env python3

"""
Universal Logging Migrator

This script helps migrate projects from various logging systems to LogLama.
Supported source logging systems:
- Standard library logging (Python's built-in logging module)
- Loguru
- structlog
- Custom logging implementations
- LogLama (already handled by migrate_to_loglama.py)

Usage:
    python universal_log_migrator.py --path /path/to/project --source logging --report-only
    python universal_log_migrator.py --path /path/to/project --source loguru
    python universal_log_migrator.py --path /path/to/project --source structlog
    python universal_log_migrator.py --path /path/to/project --source custom
"""

import argparse
import os
import re
import sys
import json
import shutil
import datetime
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union

# Import migrator modules
from migrators.base_migrator import BaseMigrator, MigrationReport
from migrators.logging_migrator import LoggingMigrator
from migrators.loguru_migrator import LoguruMigrator
from migrators.structlog_migrator import StructlogMigrator
from migrators.custom_migrator import CustomMigrator
from migrators.loglama_migrator import PylogsMigrator

# Constants
IGNORE_DIRS = {
    ".git", ".github", "__pycache__", "venv", "env", ".venv", "node_modules",
    "dist", "build", ".idea", ".vscode", ".pytest_cache"
}

IGNORE_FILES = {
    "universal_log_migrator.py",  # Don't modify this script itself
    "migrate_to_loglama.py",     # Don't modify the LogLama migrator
}


def should_ignore_path(path: Path) -> bool:
    """Check if a path should be ignored."""
    if path.is_dir() and path.name in IGNORE_DIRS:
        return True
    
    if path.is_file() and path.name in IGNORE_FILES:
        return True
    
    # Ignore binary files
    if path.is_file() and not is_text_file(path):
        return True
    
    return False


def is_text_file(path: Path) -> bool:
    """Check if a file is a text file."""
    try:
        with open(path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' not in chunk  # Binary files typically contain null bytes
    except Exception:
        return False


def get_migrator(source_type: str) -> BaseMigrator:
    """Get the appropriate migrator for the source logging system."""
    migrators = {
        "logging": LoggingMigrator(),
        "loguru": LoguruMigrator(),
        "structlog": StructlogMigrator(),
        "custom": CustomMigrator(),
        "loglama": PylogsMigrator()
    }
    
    if source_type not in migrators:
        raise ValueError(f"Unsupported source logging system: {source_type}")
    
    return migrators[source_type]


def process_directory(base_path: Path, migrator: BaseMigrator, report: MigrationReport, 
                      report_only: bool, verbose: bool):
    """Process all files in a directory recursively."""
    for root, dirs, files in os.walk(base_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            file_path = Path(root) / file
            
            if should_ignore_path(file_path):
                continue
            
            if verbose:
                print(f"Scanning file: {file_path}")
            
            migrator.process_file(file_path, report, report_only, verbose)


def rename_files(base_path: Path, migrator: BaseMigrator, report: MigrationReport, 
                 report_only: bool, verbose: bool):
    """Rename files containing source logging system references."""
    for root, dirs, files in os.walk(base_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if migrator.should_rename_file(file):
                old_path = Path(root) / file
                new_file = migrator.get_renamed_file(file)
                new_path = Path(root) / new_file
                
                if verbose:
                    print(f"Found file to rename: {old_path} -> {new_path}")
                
                report.add_change(str(old_path), "file_rename", str(old_path), str(new_path))
                
                if not report_only:
                    shutil.move(old_path, new_path)
                    if verbose:
                        print(f"Renamed file: {old_path} -> {new_path}")


def rename_directories(base_path: Path, migrator: BaseMigrator, report: MigrationReport, 
                        report_only: bool, verbose: bool):
    """Rename directories containing source logging system references."""
    # We need to process directories from deepest to shallowest to avoid renaming issues
    all_dirs = []
    
    for root, dirs, _ in os.walk(base_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for dir_name in dirs:
            if migrator.should_rename_directory(dir_name):
                all_dirs.append(Path(root) / dir_name)
    
    # Sort by depth (deepest first)
    all_dirs.sort(key=lambda p: len(p.parts), reverse=True)
    
    for old_dir in all_dirs:
        new_dir_name = migrator.get_renamed_directory(old_dir.name)
        new_dir = old_dir.parent / new_dir_name
        
        if verbose:
            print(f"Found directory to rename: {old_dir} -> {new_dir}")
        
        report.add_change(str(old_dir), "directory_rename", str(old_dir), str(new_dir))
        
        if not report_only:
            shutil.move(old_dir, new_dir)
            if verbose:
                print(f"Renamed directory: {old_dir} -> {new_dir}")


def create_loglama_config(base_path: Path, migrator: BaseMigrator, report: MigrationReport, 
                         report_only: bool, verbose: bool):
    """Create LogLama configuration files based on existing logging configuration."""
    if verbose:
        print("Creating LogLama configuration files...")
    
    migrator.create_loglama_config(base_path, report, report_only, verbose)


def update_requirements(base_path: Path, report: MigrationReport, report_only: bool, verbose: bool):
    """Update requirements.txt or pyproject.toml to include LogLama."""
    req_file = base_path / "requirements.txt"
    pyproject_file = base_path / "pyproject.toml"
    
    if req_file.exists():
        if verbose:
            print(f"Updating {req_file}...")
        
        with open(req_file, 'r') as f:
            content = f.read()
        
        # Add LogLama to requirements if not already present
        if "loglama" not in content.lower():
            new_content = content.rstrip() + "\nloglama>=1.0.0\n"
            report.add_change(str(req_file), "requirements", content, new_content)
            
            if not report_only:
                with open(req_file, 'w') as f:
                    f.write(new_content)
    
    if pyproject_file.exists():
        if verbose:
            print(f"Updating {pyproject_file}...")
        
        with open(pyproject_file, 'r') as f:
            content = f.read()
        
        # This is a simple approach - for a real implementation, you'd want to use a TOML parser
        if "loglama" not in content.lower():
            # Try to find the dependencies section
            if "[tool.poetry.dependencies]" in content:
                new_content = content.replace(
                    "[tool.poetry.dependencies]", 
                    "[tool.poetry.dependencies]\nloglama = \"^1.0.0\""
                )
                report.add_change(str(pyproject_file), "pyproject", content, new_content)
                
                if not report_only:
                    with open(pyproject_file, 'w') as f:
                        f.write(new_content)


def main():
    parser = argparse.ArgumentParser(description="Migrate from various logging systems to LogLama")
    parser.add_argument("--path", type=str, default=".", help="Path to scan for logging references")
    parser.add_argument("--source", type=str, required=True, 
                        choices=["logging", "loguru", "structlog", "custom", "loglama"],
                        help="Source logging system to migrate from")
    parser.add_argument("--report-only", action="store_true", help="Only report changes, don't modify files")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--output", type=str, default="migration_report.json", 
                        help="Output file for the migration report")
    parser.add_argument("--create-config", action="store_true", 
                        help="Create LogLama configuration files")
    parser.add_argument("--update-requirements", action="store_true", 
                        help="Update requirements.txt or pyproject.toml to include LogLama")
    
    args = parser.parse_args()
    
    base_path = Path(args.path).resolve()
    report = MigrationReport()
    
    if not base_path.exists():
        print(f"Error: Path {base_path} does not exist")
        return 1
    
    try:
        migrator = get_migrator(args.source)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    print(f"{'Analyzing' if args.report_only else 'Migrating'} from {args.source} to LogLama in {base_path}")
    
    # First scan and update file contents
    process_directory(base_path, migrator, report, args.report_only, args.verbose)
    
    # Then rename files and directories (only if not in report-only mode)
    if not args.report_only:
        rename_files(base_path, migrator, report, args.report_only, args.verbose)
        rename_directories(base_path, migrator, report, args.report_only, args.verbose)
    
    # Create LogLama configuration files if requested
    if args.create_config:
        create_loglama_config(base_path, migrator, report, args.report_only, args.verbose)
    
    # Update requirements if requested
    if args.update_requirements:
        update_requirements(base_path, report, args.report_only, args.verbose)
    
    # Generate and save report
    report_path = args.output
    report.save_report(report_path)
    
    # Print summary
    summary = report.generate_report()["summary"]
    print("\nMigration Summary:")
    print(f"Files scanned: {summary['files_scanned']}")
    print(f"Files modified: {summary['files_modified']}")
    print(f"Duration: {summary['duration_seconds']:.2f} seconds")
    print(f"Report saved to: {report_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3

"""
Migration script to update LogLama to LogLama across all projects.

This script will:
1. Scan repositories for LogLama dependencies
2. Update import statements, variable names, and function calls
3. Update environment variables and configuration files
4. Generate a report of changes made

Usage:
    python migrate_to_loglama.py [--path /path/to/scan] [--report-only] [--verbose]
"""

import argparse
import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
import shutil
import datetime

# Constants
LOGLAMA_PATTERNS = {
    "imports": r"(from|import)\s+(loglama|loglama\.[\w\.]+)",
    "function_calls": r"([\w\.]+)?(loglama[\w\.]*)\.([\w\.]+)",
    "variable_names": r"([^\w])(loglama[\w]*)",
    "logger_names": r'"(loglama[\w_]*)"\''
}

ENV_VAR_PATTERN = r"([^\w])(LOGLAMA_[\w_]*)"
CONFIG_FILE_PATTERN = r"(loglama[\w_]*\.(?:json|yaml|yml|ini|conf|cfg|toml))"

REPLACEMENT_MAP = {
    "loglama": "loglama",
    "LOGLAMA": "LOGLAMA"
}

IGNORE_DIRS = {
    ".git", ".github", "__pycache__", "venv", "env", ".venv", "node_modules",
    "dist", "build", ".idea", ".vscode", ".pytest_cache"
}

IGNORE_FILES = {
    "migrate_to_loglama.py",  # Don't modify this script itself
}


class MigrationReport:
    """Class to track and report on migration changes."""
    
    def __init__(self):
        self.files_scanned = 0
        self.files_modified = 0
        self.changes = {}
        self.start_time = datetime.datetime.now()
    
    def add_change(self, file_path: str, change_type: str, old_text: str, new_text: str):
        """Add a change to the report."""
        if file_path not in self.changes:
            self.changes[file_path] = []
        
        self.changes[file_path].append({
            "type": change_type,
            "old": old_text,
            "new": new_text
        })
    
    def increment_scanned(self):
        """Increment the count of files scanned."""
        self.files_scanned += 1
    
    def increment_modified(self):
        """Increment the count of files modified."""
        self.files_modified += 1
    
    def generate_report(self) -> Dict:
        """Generate a report of all changes made."""
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        return {
            "summary": {
                "files_scanned": self.files_scanned,
                "files_modified": self.files_modified,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration
            },
            "changes": self.changes
        }
    
    def save_report(self, output_path: str):
        """Save the report to a JSON file."""
        report = self.generate_report()
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_path


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


def scan_file(file_path: Path, report: MigrationReport, report_only: bool, verbose: bool) -> bool:
    """Scan a file for LogLama references and update them."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Skip binary files or files with encoding issues
        return False
    
    report.increment_scanned()
    
    original_content = content
    modified = False
    
    # Process imports
    for match in re.finditer(LOGLAMA_PATTERNS["imports"], content):
        import_stmt = match.group(0)
        module = match.group(2)
        new_module = module.replace("loglama", "loglama")
        new_import_stmt = import_stmt.replace(module, new_module)
        
        if verbose:
            print(f"Found import: {import_stmt} -> {new_import_stmt}")
        
        report.add_change(str(file_path), "import", import_stmt, new_import_stmt)
        content = content.replace(import_stmt, new_import_stmt)
        modified = True
    
    # Process function calls
    for match in re.finditer(LOGLAMA_PATTERNS["function_calls"], content):
        full_match = match.group(0)
        module = match.group(2)
        new_module = module.replace("loglama", "loglama")
        new_call = full_match.replace(module, new_module)
        
        if verbose:
            print(f"Found function call: {full_match} -> {new_call}")
        
        report.add_change(str(file_path), "function_call", full_match, new_call)
        content = content.replace(full_match, new_call)
        modified = True
    
    # Process variable names
    for match in re.finditer(LOGLAMA_PATTERNS["variable_names"], content):
        prefix = match.group(1)  # Capture the character before the variable name
        var_name = match.group(2)
        new_var_name = var_name.replace("loglama", "loglama")
        full_match = prefix + var_name
        new_match = prefix + new_var_name
        
        if verbose:
            print(f"Found variable: {var_name} -> {new_var_name}")
        
        report.add_change(str(file_path), "variable", var_name, new_var_name)
        content = content.replace(full_match, new_match)
        modified = True
    
    # Process logger names
    for match in re.finditer(LOGLAMA_PATTERNS["logger_names"], content):
        logger_name = match.group(1)
        new_logger_name = logger_name.replace("loglama", "loglama")
        full_match = f'"{logger_name}"'
        new_match = f'"{new_logger_name}"'
        
        if verbose:
            print(f"Found logger name: {logger_name} -> {new_logger_name}")
        
        report.add_change(str(file_path), "logger_name", logger_name, new_logger_name)
        content = content.replace(full_match, new_match)
        modified = True
    
    # Process environment variables
    for match in re.finditer(ENV_VAR_PATTERN, content):
        prefix = match.group(1)  # Capture the character before the env var
        env_var = match.group(2)
        new_env_var = env_var.replace("LOGLAMA_", "LOGLAMA_")
        full_match = prefix + env_var
        new_match = prefix + new_env_var
        
        if verbose:
            print(f"Found env var: {env_var} -> {new_env_var}")
        
        report.add_change(str(file_path), "env_var", env_var, new_env_var)
        content = content.replace(full_match, new_match)
        modified = True
    
    # Write changes back to the file if not in report-only mode
    if modified and not report_only:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        report.increment_modified()
        if verbose:
            print(f"Updated file: {file_path}")
    
    return modified


def rename_files(base_path: Path, report: MigrationReport, report_only: bool, verbose: bool):
    """Rename files containing 'loglama' in their name."""
    for root, dirs, files in os.walk(base_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if "loglama" in file.lower():
                old_path = Path(root) / file
                new_file = file.replace("loglama", "loglama").replace("LogLama", "LogLama")
                new_path = Path(root) / new_file
                
                if verbose:
                    print(f"Found file to rename: {old_path} -> {new_path}")
                
                report.add_change(str(old_path), "file_rename", str(old_path), str(new_path))
                
                if not report_only:
                    shutil.move(old_path, new_path)
                    if verbose:
                        print(f"Renamed file: {old_path} -> {new_path}")


def rename_directories(base_path: Path, report: MigrationReport, report_only: bool, verbose: bool):
    """Rename directories containing 'loglama' in their name."""
    # We need to process directories from deepest to shallowest to avoid renaming issues
    all_dirs = []
    
    for root, dirs, _ in os.walk(base_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for dir_name in dirs:
            if "loglama" in dir_name.lower():
                all_dirs.append(Path(root) / dir_name)
    
    # Sort by depth (deepest first)
    all_dirs.sort(key=lambda p: len(p.parts), reverse=True)
    
    for old_dir in all_dirs:
        new_dir_name = old_dir.name.replace("loglama", "loglama").replace("LogLama", "LogLama")
        new_dir = old_dir.parent / new_dir_name
        
        if verbose:
            print(f"Found directory to rename: {old_dir} -> {new_dir}")
        
        report.add_change(str(old_dir), "directory_rename", str(old_dir), str(new_dir))
        
        if not report_only:
            shutil.move(old_dir, new_dir)
            if verbose:
                print(f"Renamed directory: {old_dir} -> {new_dir}")


def process_directory(base_path: Path, report: MigrationReport, report_only: bool, verbose: bool):
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
            
            scan_file(file_path, report, report_only, verbose)


def main():
    parser = argparse.ArgumentParser(description="Migrate from LogLama to LogLama across projects")
    parser.add_argument("--path", type=str, default=".", help="Path to scan for LogLama references")
    parser.add_argument("--report-only", action="store_true", help="Only report changes, don't modify files")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--output", type=str, default="migration_report.json", help="Output file for the migration report")
    
    args = parser.parse_args()
    
    base_path = Path(args.path).resolve()
    report = MigrationReport()
    
    if not base_path.exists():
        print(f"Error: Path {base_path} does not exist")
        return 1
    
    print(f"{'Analyzing' if args.report_only else 'Migrating'} LogLama to LogLama in {base_path}")
    
    # First scan and update file contents
    process_directory(base_path, report, args.report_only, args.verbose)
    
    # Then rename files (only if not in report-only mode)
    if not args.report_only:
        rename_files(base_path, report, args.report_only, args.verbose)
        rename_directories(base_path, report, args.report_only, args.verbose)
    
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

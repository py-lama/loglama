#!/usr/bin/env python3

"""Decorator application tool for LogLama.

This script helps users apply LogLama decorators to their Python projects.
"""

import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from loglama.core.logger import setup_logging
from loglama.decorators.diagnostics import with_diagnostics

# Add LogLama to path if not installed
loglama_path = Path(__file__).resolve().parent.parent.parent
if loglama_path.exists():
    sys.path.insert(0, str(loglama_path))


# Setup logging
logger = setup_logging(name="loglama.decorators", level="INFO", console=True)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="LogLama Decorator Application Tool"
    )

    parser.add_argument(
        "target", help="Path to the Python file or directory to process"
    )

    parser.add_argument(
        "--decorator",
        "-d",
        choices=[
            "auto_fix",
            "with_diagnostics",
            "monitor_performance",
            "resource_usage_monitor",
            "diagnose_on_error",
            "log_errors",
            "retry",
            "fallback",
            "timeout",
        ],
        default="with_diagnostics",
        help="Decorator to apply (default: with_diagnostics)",
    )

    parser.add_argument(
        "--backup",
        "-b",
        action="store_true",
        help="Create backups of files before modifying them",
    )

    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without making changes",
    )

    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Process directories recursively",
    )

    parser.add_argument(
        "--pattern",
        "-p",
        help="Regular expression pattern to match function names",
    )

    parser.add_argument(
        "--exclude",
        "-e",
        help="Regular expression pattern to exclude function names",
    )

    parser.add_argument(
        "--params",
        help="Decorator parameters in format 'param1=value1,param2=value2'",
    )

    return parser.parse_args()


class FunctionFinder(ast.NodeVisitor):
    """AST visitor to find functions in a Python file."""

    def __init__(
        self,
        include_pattern: Optional[str] = None,
        exclude_pattern: Optional[str] = None,
    ):
        self.functions = []  # type: ignore[var-annotated,<type>]
        self.include_pattern = (
            re.compile(include_pattern) if include_pattern else None
        )
        self.exclude_pattern = (
            re.compile(exclude_pattern) if exclude_pattern else None
        )

    def visit_FunctionDef(self, node):
        # Check if function matches patterns
        include_match = (
            True
            if self.include_pattern is None
            else bool(self.include_pattern.search(node.name))
        )
        exclude_match = (
            False
            if self.exclude_pattern is None
            else bool(self.exclude_pattern.search(node.name))
        )

        if include_match and not exclude_match:
            # Check if function already has decorators
            has_loglama_decorator = False
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and hasattr(
                    decorator.func, "id"
                ):
                    if decorator.func.id in [
                        "auto_fix",
                        "with_diagnostics",
                        "monitor_performance",
                        "resource_usage_monitor",
                        "diagnose_on_error",
                        "log_errors",
                        "retry",
                        "fallback",
                        "timeout",
                    ]:
                        has_loglama_decorator = True
                        break
                elif isinstance(decorator, ast.Name):
                    if decorator.id in [
                        "auto_fix",
                        "with_diagnostics",
                        "monitor_performance",
                        "resource_usage_monitor",
                        "diagnose_on_error",
                        "log_errors",
                        "retry",
                        "fallback",
                        "timeout",
                    ]:
                        has_loglama_decorator = True
                        break

            self.functions.append(
                {
                    "name": node.name,
                    "lineno": node.lineno,
                    "has_loglama_decorator": has_loglama_decorator,
                }
            )

        self.generic_visit(node)


def find_functions_in_file(
    file_path: str,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Find functions in a Python file that match the given patterns.

    Args:
        file_path: Path to the Python file
        include_pattern: Regular expression pattern to match function names
        exclude_pattern: Regular expression pattern to exclude function names

    Returns:
        List[Dict[str, Any]]: List of functions found
    """
    try:
        with open(file_path, "r") as f:
            source = f.read()

        tree = ast.parse(source)
        finder = FunctionFinder(include_pattern, exclude_pattern)
        finder.visit(tree)

        return finder.functions
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {str(e)}")
        return []


@with_diagnostics()
def apply_decorator_to_file(
    file_path: str,
    decorator: str,
    params: Optional[Dict[str, Any]] = None,
    backup: bool = True,
    dry_run: bool = False,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply a decorator to functions in a Python file.

    Args:
        file_path: Path to the Python file
        decorator: Name of the decorator to apply
        params: Decorator parameters
        backup: Whether to create a backup of the file
        dry_run: Whether to show what would be done without making changes
        include_pattern: Regular expression pattern to match function names
        exclude_pattern: Regular expression pattern to exclude function names

    Returns:
        Dict[str, Any]: Results of the operation
    """
    result = {
        "file_path": file_path,
        "decorator": decorator,
        "functions_modified": [],
        "backup_created": False,
        "errors": [],
    }

    # Find functions in the file
    functions = find_functions_in_file(
        file_path, include_pattern, exclude_pattern
    )

    if not functions:
        logger.info(f"No matching functions found in {file_path}")
        return result

    # Filter out functions that already have LogLama decorators
    functions_to_modify = [
        f for f in functions if not f["has_loglama_decorator"]
    ]

    if not functions_to_modify:
        logger.info(
            f"All matching functions in {file_path} already have LogLama decorators"
        )
        return result

    try:
        # Read the file content
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Create backup if requested
        if backup and not dry_run:
            backup_path = f"{file_path}.bak"
            with open(backup_path, "w") as f:
                f.writelines(lines)
            result["backup_created"] = True

        # Format decorator string
        if params and len(params) > 0:
            params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            decorator_str = f"@{decorator}({params_str})\n"
        else:
            decorator_str = f"@{decorator}\n"

        # Apply decorator to each function
        # We need to process in reverse order to avoid changing line numbers
        for func in sorted(
            functions_to_modify, key=lambda x: x["lineno"], reverse=True
        ):
            lineno = func["lineno"] - 1  # Convert to 0-indexed

            # Check if we need to add imports
            if not any(
                line.strip().startswith(
                    f"from loglama.decorators.{decorator.split('_')[0]} import {decorator}"
                )
                for line in lines
            ) and not any(
                line.strip() == f"from loglama.decorators import {decorator}"
                for line in lines
            ):
                # Find the right place to add the import
                import_line = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith(
                        "import "
                    ) or line.strip().startswith("from "):
                        import_line = i + 1

                if import_line >= 0:
                    # Determine which import to add based on decorator name
                    if decorator in ["auto_fix"]:
                        import_str = "from loglama.decorators.auto_fix import auto_fix\n"
                    elif decorator in [
                        "with_diagnostics",
                        "monitor_performance",
                        "resource_usage_monitor",
                        "diagnose_on_error",
                    ]:
                        import_str = f"from loglama.decorators.diagnostics import {decorator}\n"
                    elif decorator in [
                        "log_errors",
                        "retry",
                        "fallback",
                        "timeout",
                    ]:
                        import_str = f"from loglama.decorators.error_handling import {decorator}\n"
                    else:
                        import_str = (
                            f"from loglama.decorators import {decorator}\n"
                        )

                    lines.insert(import_line, import_str)
                    # Update line numbers for remaining functions
                    for f in functions_to_modify:  # type: ignore[ Any,assignment,str]
                        if f["lineno"] > import_line + 1:  # type: ignore[_WrappedBuffer,index]
                            f["lineno"] += 1  # type: ignore[_WrappedBuffer,index]
                    lineno += 1  # Update current function line number

            # Add decorator before function definition
            lines.insert(lineno, decorator_str)
            result["functions_modified"].append(func["name"])  # type: ignore[attr-defined]

        # Write modified content back to the file
        if not dry_run:
            with open(file_path, "w") as f:
                f.writelines(lines)

        # Log results
        if dry_run:
            logger.info(
                f"[DRY RUN] Would apply {decorator} to {len(result['functions_modified'])} "  # type: ignore[arg-type]
                f"functions in {file_path}"
            )
        else:
            logger.info(
                f"Applied {decorator} to {len(result['functions_modified'])} "  # type: ignore[arg-type]
                f"functions in {file_path}"
            )

        for func_name in result["functions_modified"]:  # type: ignore[attr-defined]
            if dry_run:
                logger.info(f"[DRY RUN] Would decorate function: {func_name}")
            else:
                logger.info(f"Decorated function: {func_name}")

    except Exception as e:
        result["errors"].append(str(e))  # type: ignore[attr-defined]
        logger.error(f"Error applying decorator to {file_path}: {str(e)}")

    return result


def process_directory(
    directory: str,
    decorator: str,
    params: Optional[Dict[str, Any]] = None,
    backup: bool = True,
    dry_run: bool = False,
    recursive: bool = False,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
) -> Dict[str, Any]:
    """Process all Python files in a directory.

    Args:
        directory: Path to the directory
        decorator: Name of the decorator to apply
        params: Decorator parameters
        backup: Whether to create backups of files
        dry_run: Whether to show what would be done without making changes
        recursive: Whether to process subdirectories
        include_pattern: Regular expression pattern to match function names
        exclude_pattern: Regular expression pattern to exclude function names

    Returns:
        Dict[str, Any]: Results of the operation
    """
    result = {
        "directory": directory,
        "files_processed": 0,
        "files_modified": 0,
        "functions_modified": 0,
        "errors": [],
    }

    # Walk through the directory
    if recursive:
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories and virtual environments
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ["venv", "env", "__pycache__"]
            ]

            # Process Python files
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    file_result = apply_decorator_to_file(
                        file_path,
                        decorator,
                        params,
                        backup,
                        dry_run,
                        include_pattern,
                        exclude_pattern,
                    )

                    result["files_processed"] += 1  # type: ignore[operator]
                    if file_result["functions_modified"]:
                        result["files_modified"] += 1  # type: ignore[operator]
                        result["functions_modified"] += len(  # type: ignore[operator]
                            file_result["functions_modified"]
                        )

                    if file_result["errors"]:
                        result["errors"].extend(file_result["errors"])  # type: ignore[attr-defined]
    else:
        # Process only Python files in the current directory
        for item in os.listdir(directory):
            if item.endswith(".py"):
                file_path = os.path.join(directory, item)
                if os.path.isfile(file_path):
                    file_result = apply_decorator_to_file(
                        file_path,
                        decorator,
                        params,
                        backup,
                        dry_run,
                        include_pattern,
                        exclude_pattern,
                    )

                    result["files_processed"] += 1  # type: ignore[operator]
                    if file_result["functions_modified"]:
                        result["files_modified"] += 1  # type: ignore[operator]
                        result["functions_modified"] += len(  # type: ignore[operator]
                            file_result["functions_modified"]
                        )

                    if file_result["errors"]:
                        result["errors"].extend(file_result["errors"])  # type: ignore[attr-defined]

    return result


def parse_decorator_params(params_str: Optional[str]) -> Dict[str, Any]:
    """Parse decorator parameters from a string.

    Args:
        params_str: String in format 'param1=value1,param2=value2'

    Returns:
        Dict[str, Any]: Parsed parameters
    """
    if not params_str:
        return {}

    result = {}
    parts = params_str.split(",")

    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Convert value to appropriate type
            if value.lower() == "true":
                result[key] = True
            elif value.lower() == "false":
                result[key] = False
            elif value.isdigit():
                result[key] = int(value)  # type: ignore[assignment]
            elif value.replace(".", "", 1).isdigit():
                result[key] = float(value)  # type: ignore[assignment]
            else:
                # String value (keep quotes if present)
                if (value.startswith("'") and value.endswith("'")) or (
                    value.startswith('"') and value.endswith('"')
                ):
                    result[key] = value  # type: ignore[assignment]
                else:
                    result[key] = f'"{value}"'  # type: ignore[assignment]

    return result


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()

    # Parse decorator parameters
    params = parse_decorator_params(args.params)

    # Process target
    target_path = args.target

    if os.path.isfile(target_path):
        # Single file
        if not target_path.endswith(".py"):
            logger.error(f"Target file is not a Python file: {target_path}")
            return 1

        logger.info(f"Processing file: {target_path}")
        result = apply_decorator_to_file(
            target_path,
            args.decorator,
            params,
            args.backup,
            args.dry_run,
            args.pattern,
            args.exclude,
        )

        if result["errors"]:
            for error in result["errors"]:
                logger.error(error)
            return 1

        if not result["functions_modified"]:
            logger.info("No functions were modified")

    elif os.path.isdir(target_path):
        # Directory
        logger.info(f"Processing directory: {target_path}")
        result = process_directory(
            target_path,
            args.decorator,
            params,
            args.backup,
            args.dry_run,
            args.recursive,
            args.pattern,
            args.exclude,
        )

        if result["errors"]:
            for error in result["errors"]:
                logger.error(error)

        logger.info(f"Processed {result['files_processed']} files")
        logger.info(f"Modified {result['files_modified']} files")
        logger.info(f"Decorated {result['functions_modified']} functions")

        if result["errors"]:
            return 1
    else:
        logger.error(f"Target not found: {target_path}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

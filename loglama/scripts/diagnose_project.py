#!/usr/bin/env python3

"""Project diagnostic tool for LogLama.

This script can be used to diagnose issues in other projects using LogLama.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from loglama.core.logger import setup_logging
# Add LogLama to path if not installed
loglama_path = Path(__file__).resolve().parent.parent.parent
if loglama_path.exists():
    sys.path.insert(0, str(loglama_path))

from loglama.utils.auto_fix import (  # noqa: E402  # type: ignore[attr-defined]
    apply_fixes,
    create_loglama_config,
    detect_database_issues,
    detect_environment_issues,
    detect_logging_issues,
    fix_project_environment,
    fix_project_logging,
)

# Setup logging
logger = setup_logging(name="loglama.diagnose", level="INFO", console=True)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="LogLama Project Diagnostic Tool"
    )

    parser.add_argument(
        "project_dir", help="Path to the project directory to diagnose"
    )

    parser.add_argument(
        "--fix",
        "-",
        action="store_true",
        help="Automatically fix detected issues",
    )

    parser.add_argument(
        "--report",
        "-r",
        help="Path to save the diagnostic report (JSON format)",
    )

    parser.add_argument(
        "--backup",
        "-b",
        action="store_true",
        help="Create backups of files before modifying them",
    )

    parser.add_argument(
        "--config",
        "-c",
        action="store_true",
        help="Create a LogLama configuration file if not present",
    )

    parser.add_argument(
        "--env",
        "-e",
        action="store_true",
        help="Create or update environment file with LogLama variables",
    )

    return parser.parse_args()


def diagnose_project(project_dir: str) -> Dict[str, Any]:
    """Diagnose issues in a project.

    Args:
        project_dir: Path to the project directory

    Returns:
        Dict[str, Any]: Diagnostic report
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "project_dir": project_dir,
        "issues": [],
        "status": "healthy",
    }

    # Check if directory exists
    if not os.path.exists(project_dir) or not os.path.isdir(project_dir):
        report["issues"].append(  # type: ignore[attr-defined,str]
            {
                "type": "invalid_project_dir",
                "message": f"Project directory not found: {project_dir}",
                "params": {},
            }
        )
        report["status"] = "error"
        return report

    # Scan Python files for logging issues
    logger.info(f"Scanning project directory: {project_dir}")
    python_files = []
    for root, _, files in os.walk(project_dir):
        # Skip hidden directories and virtual environments
        if any(part.startswith(".") for part in root.split(os.sep)) or any(
            venv in root for venv in ["venv", "env", "__pycache__"]
        ):
            continue

        # Collect Python files
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    logger.info(f"Found {len(python_files)} Python files")

    # Check for logging issues in each file
    for file_path in python_files:
        file_issues = detect_logging_issues(file_path)
        if file_issues:
            report["issues"].extend(file_issues)  # type: ignore[attr-defined,str]

    # Check for database issues
    db_paths = []
    for root, _, files in os.walk(project_dir):
        for file in files:
            if (
                file.endswith(".db")
                or file.endswith(".sqlite")
                or file.endswith(".sqlite3")
            ):
                db_paths.append(os.path.join(root, file))

    if db_paths:
        logger.info(f"Found {len(db_paths)} database files")
        for db_path in db_paths:
            db_issues = detect_database_issues(db_path)
            if db_issues:
                report["issues"].extend(db_issues)  # type: ignore[attr-defined,str]

    # Check for environment issues
    env_issues = detect_environment_issues()
    if env_issues:
        report["issues"].extend(env_issues)  # type: ignore[attr-defined,str]

    # Check for configuration files
    config_files = [
        os.path.join(project_dir, ".env"),
        os.path.join(project_dir, "loglama.yaml"),
        os.path.join(project_dir, "loglama.yml"),
        os.path.join(project_dir, "logging.con"),
        os.path.join(project_dir, "logging.yaml"),
    ]

    found_config = False
    for config_file in config_files:
        if os.path.exists(config_file):
            found_config = True
            break

    if not found_config:
        report["issues"].append(  # type: ignore[attr-defined,str]
            {
                "type": "missing_config",
                "message": "No LogLama configuration file found",
                "params": {"project_dir": project_dir},
            }
        )

    # Update status if issues were found
    if report["issues"]:
        report["status"] = "issues_found"

    return report


def fix_project_issues(
    project_dir: str, report: Dict[str, Any], backup: bool = True
) -> Dict[str, Any]:
    """Fix issues in a project.

    Args:
        project_dir: Path to the project directory
        report: Diagnostic report
        backup: Whether to backup files before modifying them

    Returns:
        Dict[str, Any]: Fix results
    """
    results = {"fixed_issues": [], "failed_fixes": [], "modified_files": []}  # type: ignore[var-annotated]

    # Skip if no issues found
    if not report["issues"]:
        logger.info("No issues to fix")
        return results

    # Fix logging issues
    logging_fix_results = fix_project_logging(project_dir, backup)

    if logging_fix_results["modified_files"] > 0:
        results["fixed_issues"].append(
            {
                "type": "logging_issues",
                "message": f"Fixed logging issues in {logging_fix_results['modified_files']} files",
                "details": logging_fix_results,
            }
        )
        results["modified_files"].extend(
            logging_fix_results["modified_files_list"]
        )

    if logging_fix_results["errors"]:
        results["failed_fixes"].append(
            {
                "type": "logging_issues",
                "message": "Failed to fix some logging issues",
                "details": logging_fix_results["errors"],
            }
        )

    # Apply fixes for other issues
    fixable_issues = [
        issue
        for issue in report["issues"]
        if issue["type"]
        in [
            "missing_file_permissions",
            "database_connection_error",
            "invalid_log_level",
            "missing_environment_variable",
        ]
    ]

    if fixable_issues:
        fix_results = apply_fixes(fixable_issues)

        if fix_results["fixed"]:
            results["fixed_issues"].append(
                {
                    "type": "general_issues",
                    "message": f"Fixed {len(fix_results['fixed'])} general issues",
                    "details": fix_results["fixed"],
                }
            )

        if fix_results["failed"]:
            results["failed_fixes"].append(
                {
                    "type": "general_issues",
                    "message": f"Failed to fix {len(fix_results['failed'])} general issues",
                    "details": fix_results["failed"],
                }
            )

    return results


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()

    # Diagnose project
    logger.info(f"Diagnosing project: {args.project_dir}")
    report = diagnose_project(args.project_dir)

    # Display results
    if report["status"] == "healthy":
        logger.info("No issues found in the project")
    else:
        logger.warning(f"Found {len(report['issues'])} issues in the project")
        for i, issue in enumerate(report["issues"], 1):
            logger.warning(f"{i}. {issue['type']}: {issue['message']}")

    # Fix issues if requested
    if args.fix and report["issues"]:
        logger.info("Fixing issues...")
        fix_results = fix_project_issues(args.project_dir, report, args.backup)

        if fix_results["fixed_issues"]:
            logger.info(
                f"Fixed {len(fix_results['fixed_issues'])} issue types"
            )
            for fix in fix_results["fixed_issues"]:
                logger.info(f"- {fix['message']}")

        if fix_results["failed_fixes"]:
            logger.warning(
                f"Failed to fix {len(fix_results['failed_fixes'])} issue types"
            )
            for fail in fix_results["failed_fixes"]:
                logger.warning(f"- {fail['message']}")

        if fix_results["modified_files"]:
            logger.info(f"Modified {len(fix_results['modified_files'])} files")

    # Create environment file if requested
    if args.env:
        logger.info("Creating/updating environment file...")
        env_results = fix_project_environment(args.project_dir)

        if env_results["env_file_created"]:
            logger.info(
                f"Created environment file: {env_results['env_file_path']}"
            )
        elif env_results["env_file_updated"]:
            logger.info(
                f"Updated environment file: {env_results['env_file_path']}"
            )
            logger.info(
                f"Added variables: {', '.join(env_results['added_variables'])}"
            )

        if env_results["errors"]:
            for error in env_results["errors"]:
                logger.error(error)

    # Create configuration file if requested
    if args.config:
        logger.info("Creating LogLama configuration file...")
        config_results = create_loglama_config(args.project_dir)

        if config_results["config_file_created"]:
            logger.info(
                f"Created configuration file: {config_results['config_file_path']}"
            )

        if config_results["errors"]:
            for error in config_results["errors"]:
                logger.error(error)

    # Save report if requested
    if args.report:
        try:
            # Create directory if it doesn't exist
            report_dir = os.path.dirname(args.report)
            if report_dir and not os.path.exists(report_dir):
                os.makedirs(report_dir, exist_ok=True)

            # Add fix results to report if fixes were applied
            if args.fix and report["issues"]:
                report["fix_results"] = fix_project_issues(
                    args.project_dir, report, args.backup
                )

            # Save report
            with open(args.report, "w") as f:
                json.dump(report, f, indent=2)

            logger.info(f"Diagnostic report saved to: {args.report}")
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

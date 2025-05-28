#!/usr/bin/env python3

"""
Migrator for LogLama.

This migrator converts code using LogLama to use LogLama instead.
It's a wrapper around the migrate_to_loglama.py script.
"""

import os
import re
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union

from .base_migrator import BaseMigrator, MigrationReport


class PylogsMigrator(BaseMigrator):
    """Migrator for LogLama.
    
    This is a wrapper around the migrate_to_loglama.py script.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "loglama"
        self.file_patterns = [r"loglama[_\-]?config\.py", r"log[_\-]?config\.py"]
        self.dir_patterns = [r"loglama"]
        
        # Import the migrate_to_loglama module dynamically
        self.migrate_module = None
        try:
            # Try to import from the parent directory
            script_dir = Path(__file__).parent.parent
            migrate_path = script_dir / "migrate_to_loglama.py"
            
            if migrate_path.exists():
                spec = importlib.util.spec_from_file_location("migrate_to_loglama", migrate_path)
                self.migrate_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.migrate_module)
        except Exception as e:
            print(f"Warning: Could not import migrate_to_loglama.py: {e}")
    
    def migrate_content(self, content: str, file_path: Path, report: MigrationReport, verbose: bool) -> str:
        """Migrate LogLama references in the content.
        
        This delegates to the migrate_to_loglama.py script's functionality.
        """
        if self.migrate_module is None:
            print("Warning: migrate_to_loglama.py module not available, skipping content migration")
            return content
        
        try:
            # Use the patterns and functions from migrate_to_loglama.py
            migrated_content = content
            
            # Update imports
            for match in re.finditer(self.migrate_module.LOGLAMA_PATTERNS["imports"], content):
                import_stmt = match.group(0)
                module = match.group(2)
                new_module = module.replace("loglama", "loglama")
                new_import = import_stmt.replace(module, new_module)
                
                report.add_change(str(file_path), "import", import_stmt, new_import)
                migrated_content = migrated_content.replace(import_stmt, new_import)
            
            # Update from imports
            for match in re.finditer(self.migrate_module.LOGLAMA_PATTERNS["from_imports"], content):
                import_stmt = match.group(0)
                module = match.group(1)
                new_module = module.replace("loglama", "loglama")
                new_import = import_stmt.replace(module, new_module)
                
                report.add_change(str(file_path), "from_import", import_stmt, new_import)
                migrated_content = migrated_content.replace(import_stmt, new_import)
            
            # Update environment variables
            for match in re.finditer(self.migrate_module.LOGLAMA_PATTERNS["env_vars"], content):
                env_var = match.group(0)
                var_name = match.group(1)
                new_var_name = var_name.replace("LOGLAMA", "LOGLAMA")
                new_env_var = env_var.replace(var_name, new_var_name)
                
                report.add_change(str(file_path), "env_var", env_var, new_env_var)
                migrated_content = migrated_content.replace(env_var, new_env_var)
            
            # Update config keys
            for match in re.finditer(self.migrate_module.LOGLAMA_PATTERNS["config_keys"], content):
                config_key = match.group(0)
                key_name = match.group(1)
                new_key_name = key_name.replace("loglama", "loglama")
                new_config_key = config_key.replace(key_name, new_key_name)
                
                report.add_change(str(file_path), "config_key", config_key, new_config_key)
                migrated_content = migrated_content.replace(config_key, new_config_key)
            
            return migrated_content
        except Exception as e:
            print(f"Error migrating content with migrate_to_loglama.py: {e}")
            return content
    
    def get_renamed_file(self, file_name: str) -> str:
        """Get the new name for a file."""
        if re.search(r"loglama[_\-]?config\.py", file_name, re.IGNORECASE):
            return "logging_config.py"
        elif re.search(r"log[_\-]?config\.py", file_name, re.IGNORECASE):
            return "logging_config.py"
        return file_name
    
    def get_renamed_directory(self, dir_name: str) -> str:
        """Get the new name for a directory."""
        if dir_name.lower() == "loglama":
            return "logging"
        return dir_name
    
    def create_loglama_config(self, base_path: Path, report: MigrationReport, report_only: bool, verbose: bool):
        """Create LogLama configuration files based on existing logging configuration."""
        # Look for existing logging configuration files
        config_files = []
        for root, _, files in os.walk(base_path):
            for file in files:
                if re.search(r"loglama[_\-]?config\.py", file, re.IGNORECASE) or \
                   re.search(r"log[_\-]?config\.py", file, re.IGNORECASE):
                    config_files.append(Path(root) / file)
        
        if not config_files:
            # Create a new logging_config.py if none exists
            config_file = base_path / "logging_config.py"
            config_content = self._generate_default_config()
            
            if verbose:
                print(f"Creating new LogLama configuration file: {config_file}")
            
            report.add_change(str(config_file), "new_file", "", config_content)
            
            if not report_only:
                with open(config_file, 'w') as f:
                    f.write(config_content)
        else:
            # We've already migrated existing config files in the migrate_content method
            if verbose:
                print(f"Found existing logging configuration files: {config_files}")
    
    def _generate_default_config(self) -> str:
        """Generate a default LogLama configuration file."""
        return """
#!/usr/bin/env python3

"""
Logging configuration for the application.

This module initializes LogLama and provides functions for getting loggers.
"""

import os
import sys
from pathlib import Path

# Import LogLama
from loglama import setup_logging, get_logger, LogContext
from loglama.config.env_loader import load_env, get_env
from loglama.formatters import ColoredFormatter, JSONFormatter
from loglama.handlers import SQLiteHandler, EnhancedRotatingFileHandler


def init_logging():
    """Initialize logging for the application."""
    # Load environment variables from .env file
    load_env(verbose=True)
    
    # Get configuration from environment variables
    log_level = get_env("LOGLAMA_LOG_LEVEL", "INFO")
    log_dir = get_env("LOGLAMA_LOG_DIR", "./logs")
    db_logging = get_env("LOGLAMA_DB_LOGGING", "false").lower() == "true"
    db_path = get_env("LOGLAMA_DB_PATH", f"{log_dir}/app.db")
    json_logs = get_env("LOGLAMA_JSON_LOGS", "false").lower() == "true"
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup logging with LogLama
    logger = setup_logging(
        name="app",
        level=log_level,
        console=True,
        file=True,
        file_path=f"{log_dir}/app.log",
        database=db_logging,
        db_path=db_path,
        json_format=json_logs
    )
    
    logger.info("Logging initialized with LogLama")
    return logger


def get_app_logger(name):
    """Get a logger for the application.
    
    Args:
        name: Name of the logger
        
    Returns:
        A logger instance
    """
    return get_logger(name)
"""

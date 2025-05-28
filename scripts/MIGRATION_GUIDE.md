# LogLama to LogLama Migration Guide

This guide provides instructions for migrating projects from LogLama to LogLama.

## Overview

The LogLama package has been renamed to LogLama to better align with the PyLama ecosystem naming convention. This guide will help you update your projects to use the new package name.

## Automated Migration

We've provided a migration script that can automatically update your codebase to use LogLama instead of LogLama.

### Using the Migration Script

```bash
# Install LogLama if you haven't already
pip install loglama

# Run the migration script in report-only mode first to see what would change
python migrate_to_loglama.py --path /path/to/your/project --report-only --verbose

# When you're ready to make the changes, run without the --report-only flag
python migrate_to_loglama.py --path /path/to/your/project --verbose
```

### What the Migration Script Does

The script will:

1. Update import statements from `import loglama` to `import loglama`
2. Update module references from `loglama.xyz` to `loglama.xyz`
3. Update variable names containing `loglama` to use `loglama` instead
4. Update function calls like `loglama_get_logger()` to `loglama_get_logger()`
5. Update logger names (e.g., from "loglama_examples" to "loglama_examples")
6. Update environment variable references from `LOGLAMA_` to `LOGLAMA_`
7. Update configuration file names from `loglama_config.json` to `loglama_config.json`
8. Rename files and directories containing `loglama` in their names

## Manual Migration Checklist

If you prefer to manually update your code or if the migration script doesn't catch everything, here's a checklist of items to update:

### 1. Code Updates

- [ ] Update import statements from `import loglama` to `import loglama`
- [ ] Update module references from `loglama.xyz` to `loglama.xyz`
- [ ] Update variable names containing `loglama` to use `loglama` instead
- [ ] Update function calls like `loglama_get_logger()` to `loglama_get_logger()`
- [ ] Update logger names (e.g., from "loglama_examples" to "loglama_examples")

### 2. Configuration Updates

- [ ] Update environment variable references from `LOGLAMA_` to `LOGLAMA_`
- [ ] Update configuration file names from `loglama_config.json` to `loglama_config.json`
- [ ] Update diagnostic report file names from `loglama_diagnostic_report.json` to `loglama_diagnostic_report.json`

### 3. Build and Deployment Updates

- [ ] Update requirements.txt or pyproject.toml to reference `loglama` instead of `loglama`
- [ ] Update Docker files that might reference `loglama`
- [ ] Update CI/CD pipeline configurations

### 4. Documentation Updates

- [ ] Update README files to reference LogLama instead of LogLama
- [ ] Update code examples in documentation
- [ ] Update API documentation references

## Compatibility Layer

If you need to maintain compatibility with both LogLama and LogLama during a transition period, you can use the following pattern:

```python
try:
    import loglama as logging_lib
except ImportError:
    import loglama as logging_lib

# Then use logging_lib throughout your code
logger = logging_lib.get_logger(__name__)
```

## Common Issues and Solutions

### Environment Variables

If your application relies on environment variables with the `LOGLAMA_` prefix, you'll need to update your environment configuration files (.env files, Docker environment variables, CI/CD secrets, etc.) to use the `LOGLAMA_` prefix.

### Database Schema

If you're using the SQLite handler, the database schema remains the same, so existing log databases will continue to work with LogLama.

### Web Interface

The web interface URL has changed from `/loglama/` to `/loglama/`. Update any bookmarks or links accordingly.

## Getting Help

If you encounter any issues during migration, please open an issue on the [LogLama GitHub repository](https://github.com/py-lama/loglama).

## Verification

After migration, verify that logging works correctly by running your application and checking that logs are being generated as expected.

```python
from loglama import get_logger

logger = get_logger(__name__)
logger.info("If you can see this message in your logs, LogLama is working correctly!")
```

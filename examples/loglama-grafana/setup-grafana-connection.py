#!/usr/bin/env python3
"""
Setup Grafana Connection with LogLama

This script creates a proper connection between LogLama and Grafana by:
1. Creating a Grafana datasource configuration
2. Creating a dashboard for LogLama logs
3. Providing instructions for accessing the integration
"""

import os
import subprocess
import sys
import time

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_color(color, message):
    """Print colored message"""
    print(f"{color}{message}{NC}")

def run_command(command):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def setup_grafana_provisioning():
    """Set up Grafana provisioning for automatic datasource and dashboard"""
    print_color(BLUE, "Setting up Grafana provisioning...")
    
    # Create directories
    os.makedirs("grafana-provisioning/datasources", exist_ok=True)
    os.makedirs("grafana-provisioning/dashboards", exist_ok=True)
    
    # Create datasource configuration
    with open("grafana-provisioning/datasources/loglama.yml", "w") as f:
        f.write("""apiVersion: 1

datasources:
  - name: LogLama
    type: frser-sqlite-datasource
    access: proxy
    uid: loglama
    isDefault: true
    jsonData:
      path: /logs/loglama.db
    version: 1
    editable: true
""")
    
    # Create dashboard configuration
    with open("grafana-provisioning/dashboards/dashboard.yml", "w") as f:
        f.write("""apiVersion: 1

providers:
  - name: 'LogLama Dashboards'
    orgId: 1
    folder: 'LogLama'
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
""")
    
    # Create dashboard JSON
    with open("grafana-provisioning/dashboards/loglama-dashboard.json", "w") as f:
        f.write("""{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "grafana",
          "uid": "-- Grafana --"
        },
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "datasource": {
        "type": "frser-sqlite-datasource",
        "uid": "loglama"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 0,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "auto",
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 24,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "title": "Log Levels Over Time",
      "type": "timeseries",
      "targets": [
        {
          "datasource": {
            "type": "frser-sqlite-datasource",
            "uid": "loglama"
          },
          "queryText": "SELECT timestamp as time, count(*) as value, level as metric FROM logs GROUP BY level, strftime('%Y-%m-%d %H:%M', timestamp) ORDER BY timestamp;",
          "queryType": "table",
          "rawQueryText": "SELECT timestamp as time, count(*) as value, level as metric FROM logs GROUP BY level, strftime('%Y-%m-%d %H:%M', timestamp) ORDER BY timestamp;",
          "refId": "A",
          "timeColumns": ["time"]
        }
      ]
    },
    {
      "datasource": {
        "type": "frser-sqlite-datasource",
        "uid": "loglama"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "custom": {
            "align": "auto",
            "cellOptions": {
              "type": "auto"
            },
            "inspect": false
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": "WARNING"
              },
              {
                "color": "red",
                "value": "ERROR"
              },
              {
                "color": "purple",
                "value": "CRITICAL"
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byName",
              "options": "level"
            },
            "properties": [
              {
                "id": "custom.cellOptions",
                "value": {
                  "type": "color-text"
                }
              },
              {
                "id": "mappings",
                "value": [
                  {
                    "options": {
                      "DEBUG": {
                        "color": "blue",
                        "index": 0
                      },
                      "ERROR": {
                        "color": "red",
                        "index": 2
                      },
                      "INFO": {
                        "color": "green",
                        "index": 1
                      },
                      "WARNING": {
                        "color": "orange",
                        "index": 3
                      }
                    },
                    "type": "value"
                  }
                ]
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 16,
        "w": 24,
        "x": 0,
        "y": 8
      },
      "id": 2,
      "options": {
        "cellHeight": "sm",
        "footer": {
          "countRows": false,
          "fields": "",
          "reducer": ["sum"],
          "show": false
        },
        "showHeader": true
      },
      "pluginVersion": "10.0.0",
      "targets": [
        {
          "datasource": {
            "type": "frser-sqlite-datasource",
            "uid": "loglama"
          },
          "queryText": "SELECT timestamp, level, logger, message FROM logs ORDER BY timestamp DESC LIMIT 100;",
          "queryType": "table",
          "rawQueryText": "SELECT timestamp, level, logger, message FROM logs ORDER BY timestamp DESC LIMIT 100;",
          "refId": "A",
          "timeColumns": ["timestamp"]
        }
      ],
      "title": "Recent Logs",
      "type": "table"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 38,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "LogLama Dashboard",
  "uid": "loglama-dashboard",
  "version": 1,
  "weekStart": ""
}""")
    
    print_color(GREEN, "Grafana provisioning set up successfully")

def update_docker_compose():
    """Update docker-compose.yml to include Grafana provisioning"""
    print_color(BLUE, "Updating Docker Compose configuration...")
    
    with open("docker-compose.simple.yml", "r") as f:
        content = f.read()
    
    # Add provisioning volumes if not already present
    if "grafana-provisioning/datasources" not in content:
        content = content.replace(
            "      - ./logs:/logs:ro",
            "      - ./logs:/logs:ro\n      - ./grafana-provisioning/datasources:/etc/grafana/provisioning/datasources:ro\n      - ./grafana-provisioning/dashboards:/etc/grafana/provisioning/dashboards:ro"
        )
    
    with open("docker-compose.simple.yml", "w") as f:
        f.write(content)
    
    print_color(GREEN, "Docker Compose configuration updated")

def restart_containers():
    """Restart the Docker containers"""
    print_color(BLUE, "Restarting Docker containers...")
    
    run_command("docker compose -f docker-compose.simple.yml down")
    run_command("docker compose -f docker-compose.simple.yml up -d")
    
    # Wait for containers to start
    time.sleep(5)
    
    # Check if containers are running
    success, output = run_command("docker ps | grep loglama")
    if not success or "Up" not in output:
        print_color(RED, "LogLama container is not running properly")
        run_command("docker logs loglama")
        return False
    
    success, output = run_command("docker ps | grep grafana")
    if not success or "Up" not in output:
        print_color(RED, "Grafana container is not running properly")
        run_command("docker logs grafana")
        return False
    
    print_color(GREEN, "Containers restarted successfully")
    return True

def generate_sample_logs():
    """Generate sample logs using the LogLama container"""
    print_color(BLUE, "Generating sample logs in LogLama container...")
    
    # Create a Python script to generate logs
    script = """
import sqlite3
import random
import datetime
import time
import os

# Connect to the SQLite database
db_path = '/logs/loglama.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create logs table if it doesn't exist
cursor.execute(\"\"\"
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    level TEXT,
    logger TEXT,
    message TEXT,
    source TEXT,
    line INTEGER,
    function TEXT,
    extra TEXT
)
\"\"\")
conn.commit()

# Log levels
log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
loggers = ['loglama.web', 'loglama.api', 'app.main', 'app.auth', 'system']

# Generate historical logs (past 3 days)
print('Generating historical logs...')
now = datetime.datetime.now()
for day in range(3, 0, -1):
    for hour in range(0, 24, 4):  # Every 4 hours to reduce volume
        log_time = now - datetime.timedelta(days=day, hours=24-hour)
        timestamp = log_time.strftime('%Y-%m-%d %H:%M:%S')
        # Generate 5-10 logs per time period
        for _ in range(random.randint(5, 10)):
            level = random.choices(log_levels, weights=[0.5, 0.3, 0.15, 0.04, 0.01], k=1)[0]
            logger = random.choice(loggers)
            message = f'Sample {level} log message from {logger}'
            cursor.execute(\"INSERT INTO logs (timestamp, level, logger, message, source, line, function, extra) VALUES (?, ?, ?, ?, ?, ?, ?, ?)\",
                (timestamp, level, logger, message, f'{logger}.py', random.randint(10, 100), 'process_request', '{}'))

# Generate real-time logs
print('Generating real-time logs...')
for i in range(20):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    level = random.choices(log_levels, weights=[0.5, 0.3, 0.15, 0.04, 0.01], k=1)[0]
    logger = random.choice(loggers)
    message = f'Real-time {level} log message #{i} from {logger}'
    cursor.execute(\"INSERT INTO logs (timestamp, level, logger, message, source, line, function, extra) VALUES (?, ?, ?, ?, ?, ?, ?, ?)\",
        (timestamp, level, logger, message, f'{logger}.py', random.randint(10, 100), 'process_request', '{}'))
    print(f'  {timestamp} - {level} - {logger}: {message}')
    time.sleep(0.1)

conn.commit()
count = cursor.execute('SELECT COUNT(*) FROM logs').fetchone()[0]
print(f'Generated {count} total log entries')
conn.close()
"""
    
    # Run the script in the LogLama container
    cmd = f"docker exec loglama python3 -c '{script}'"
    success, output = run_command(cmd)
    
    if not success:
        print_color(RED, "Failed to generate sample logs:")
        print(output)
        return False
    
    print_color(GREEN, "Sample logs generated successfully")
    return True

def open_browser():
    """Open browser to access LogLama and Grafana"""
    print_color(BLUE, "Opening web browsers...")
    
    try:
        import webbrowser
        webbrowser.open("http://localhost:5000")
        time.sleep(1)
        webbrowser.open("http://localhost:3001")
    except Exception as e:
        print_color(YELLOW, f"Failed to open browser: {e}")
        print_color(YELLOW, "Please manually open http://localhost:5000 and http://localhost:3001")

def print_instructions():
    """Print instructions for using LogLama and Grafana"""
    print("\n" + "-"*80)
    print_color(GREEN, "LogLama-Grafana Connection Setup Complete!")
    print("-"*80)
    
    print("\nAccess Information:")
    print_color(BLUE, "LogLama Web UI: http://localhost:5000")
    print_color(BLUE, "Grafana Dashboard: http://localhost:3001")
    print_color(YELLOW, "  - Default login: admin / admin")
    
    print("\nTo view logs:")
    print_color(YELLOW, "  docker compose -f docker-compose.simple.yml logs -f")
    
    print("\nTo stop the services:")
    print_color(YELLOW, "  docker compose -f docker-compose.simple.yml down")
    
    print("\nTo create a Grafana connection to LogLama:")
    print("1. Log into Grafana at http://localhost:3001 with admin/admin")
    print("2. Go to Connections > Data Sources > Add data source")
    print("3. Select 'SQLite'")
    print("4. Configure with these settings:")
    print_color(YELLOW, "   - Name: LogLama")
    print_color(YELLOW, "   - Path: /logs/loglama.db")
    print("5. Click 'Save & Test'")
    print("6. Create a new dashboard with SQL queries like:")
    print_color(YELLOW, "   SELECT timestamp as time, level, logger, message FROM logs ORDER BY timestamp DESC LIMIT 100")
    
    print("\nFor more information, see the documentation files:")
    print_color(BLUE, "  - GRAFANA_CONNECTION_GUIDE.md")
    print_color(BLUE, "  - INTEGRATION_GUIDE.md")
    print_color(BLUE, "  - PUBLISHING_GUIDE.md")

def create_publishing_documentation():
    """Create documentation for publishing LogLama with Grafana integration"""
    print_color(BLUE, "Creating publishing documentation...")
    
    # Create a simple README for the package
    with open("PACKAGE_README.md", "w") as f:
        f.write("""# LogLama with Grafana Integration

## Overview

This package provides integration between LogLama (a centralized logging system for the PyLama ecosystem) and Grafana (a powerful visualization and monitoring platform).

## Features

- Centralized log collection with LogLama
- Beautiful log visualization with Grafana
- Pre-configured dashboards for log analysis
- Easy setup with Docker Compose

## Quick Start

```bash
# Clone the repository
git clone https://github.com/py-lama/loglama.git
cd loglama/examples/loglama-grafana

# Run the setup script
./setup-grafana-connection.py
```

## Manual Setup

See the [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for detailed instructions.

## Connecting to Grafana

See the [GRAFANA_CONNECTION_GUIDE.md](GRAFANA_CONNECTION_GUIDE.md) for detailed instructions on setting up the Grafana connection.

## Publishing

See the [PUBLISHING_GUIDE.md](PUBLISHING_GUIDE.md) for instructions on publishing this package.

## License

MIT
""")
    
    # Create a setup.py file for packaging
    with open("setup.py", "w") as f:
        f.write("""from setuptools import setup, find_packages

with open("PACKAGE_README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="loglama-grafana",
    version="0.1.0",
    author="PyLama Team",
    author_email="devlama@example.com",
    description="LogLama integration with Grafana",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/py-lama/loglama",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        'loglama',
        'flask',
        'sqlite3-utils',
    ],
    include_package_data=True,
    package_data={
        '': ['docker-compose.simple.yml', 'Dockerfile.simple', '*.md', 'grafana-provisioning/**/*'],
    },
)
""")
    
    print_color(GREEN, "Publishing documentation created successfully")

def main():
    """Main function"""
    print_color(GREEN, "=== LogLama-Grafana Connection Setup ===")
    
    # Set up Grafana provisioning
    setup_grafana_provisioning()
    
    # Update docker-compose.yml
    update_docker_compose()
    
    # Restart containers
    if not restart_containers():
        return 1
    
    # Generate sample logs
    if not generate_sample_logs():
        return 1
    
    # Create publishing documentation
    create_publishing_documentation()
    
    # Print instructions
    print_instructions()
    
    # Open browser
    open_browser()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

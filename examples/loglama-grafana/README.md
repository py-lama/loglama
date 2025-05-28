# LogLama + Grafana Example (Docker Compose)

This example demonstrates how to run LogLama and Grafana together using Docker Compose. Grafana can be configured to visualize logs or metrics produced by LogLama.

## Prerequisites
- Docker and Docker Compose installed
- (Optional) A LogLama Docker image. If not available, you may need to build one from the LogLama source/Dockerfile.

## Usage

1. Clone this repository or copy the example directory.
2. Place a valid `.env` file for LogLama as `devlama.env` in this directory if needed.
3. Start the services:
   ```bash
   docker compose up -d
   ```
4. Access LogLama at [http://localhost:5000](http://localhost:5000)
5. Access Grafana at [http://localhost:3000](http://localhost:3000)
   - Default login: `admin` / `admin`

## Grafana Integration

LogLama stores logs in files and SQLite. Grafana can visualize data from supported datasources:

- **SQLite**: Use the [SQLite datasource plugin](https://grafana.com/grafana/plugins/frser-sqlite-datasource/) to connect to LogLama's SQLite database.
- **File**: For log files, use the [Loki](https://grafana.com/oss/loki/) stack or a sidecar to tail logs and send them to Grafana/Loki.
- **Prometheus**: If LogLama exposes metrics in Prometheus format, add Prometheus as a service and datasource.

### Example: Connecting Grafana to LogLama SQLite
1. Install the SQLite datasource plugin in Grafana.
2. Configure the datasource to point to `/logs/loglama.db` (mount this volume in the Grafana container if needed).
3. Create dashboards/queries in Grafana using SQL.

### Example: File-based Log Integration (Loki)
1. Add a Loki service to `docker-compose.yml` and configure it to read from `/logs`.
2. Add Loki as a datasource in Grafana.
3. Visualize logs in Grafana using the Explore tab.

## Notes
- This example assumes the LogLama Docker image writes logs to `/logs` and/or a SQLite DB at `/logs/loglama.db`.
- You may need to adjust volume mounts and permissions for Grafana to read logs or databases.
- For advanced setups, consider adding Prometheus, Loki, or other exporters.

## Cleanup
```bash
docker compose down -v
```

---

For more details, see the main LogLama documentation and the Grafana plugin docs.

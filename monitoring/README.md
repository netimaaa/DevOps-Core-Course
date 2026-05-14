# Monitoring Stack - Loki, Promtail, Grafana

Centralized logging solution for containerized applications using Grafana Loki stack.

## Quick Start

### Prerequisites
- Docker and Docker Compose v2
- Python app image: `netimaaa/devops-app:latest`

### Deploy

```bash
# Start the stack
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Access Services

- **Grafana**: http://localhost:3000 (admin/admin)
- **Loki API**: http://localhost:3100
- **Promtail**: http://localhost:9080
- **Python App**: http://localhost:8000

### Configure Grafana

1. Login to Grafana at http://localhost:3000
2. Go to **Connections** → **Data sources** → **Add data source** → **Loki**
3. Set URL: `http://loki:3100`
4. Click **Save & Test**

### Test Logging

```bash
# Generate traffic
for i in {1..20}; do curl http://localhost:8000/; done
for i in {1..20}; do curl http://localhost:8000/health; done
```

### Query Logs

In Grafana Explore, try these LogQL queries:

```logql
# All logs from Python app
{app="devops-python"}

# Only errors
{app="devops-python"} | json | level="ERROR"

# Request rate
rate({app="devops-python"}[1m])
```

## Architecture

- **Loki 3.0**: Log storage with TSDB (7-day retention)
- **Promtail 3.0**: Log collector with Docker service discovery
- **Grafana 12.3.1**: Visualization and dashboards
- **Python App**: FastAPI app with JSON logging

## Documentation

See [docs/LAB07.md](docs/LAB07.md) for complete documentation including:
- Detailed architecture
- Configuration explanations
- Dashboard setup
- LogQL query examples
- Troubleshooting

## Stack Management

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart a service
docker compose restart loki

# View logs
docker compose logs -f loki

# Remove everything (including data)
docker compose down -v
```

## Security Notes

- Grafana anonymous auth is disabled
- Default admin password: `admin` (change via `GRAFANA_ADMIN_PASSWORD` env var)
- Docker socket mounted read-only for Promtail
- All services on isolated `logging` network

## Resource Usage

- Loki: 1 CPU, 1GB RAM
- Grafana: 1 CPU, 1GB RAM
- Promtail: 0.5 CPU, 512MB RAM
- App: 0.5 CPU, 512MB RAM
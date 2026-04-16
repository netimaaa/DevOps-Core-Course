# DevOps Info Service

[![Python CI/CD Pipeline](https://github.com/netimaaa/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/netimaaa/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/netimaaa/DevOps-Core-Course/branch/master/graph/badge.svg)](https://codecov.io/gh/netimaaa/DevOps-Core-Course)

A production-ready Python web service that provides comprehensive system information, health status monitoring, and a persisted visits counter. Built with FastAPI for the DevOps Core Course.

## Overview

This service reports detailed information about itself and its runtime environment, including:
- Service metadata (name, version, framework)
- System information (hostname, platform, architecture, CPU count)
- Runtime statistics (uptime, current time, timezone)
- Request details (client IP, user agent, HTTP method)
- Available API endpoints
- Persisted visits counter stored in a file

## Prerequisites

- **Python**: 3.11 or higher
- **pip**: Latest version recommended
- **Virtual environment**: Recommended for dependency isolation

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd DevOps-Core-Course/app_python
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Default Configuration

Run with default settings (host: 0.0.0.0, port: 8000):

```bash
python app.py
```

The service will be available at `http://localhost:8000`

By default, the visits counter is stored in `./data/visits`.

### Custom Configuration

Use environment variables to customize the service:

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py

# Custom visits file location
VISITS_FILE=/tmp/devops-visits python app.py
```

### Using Uvicorn Directly

You can also run the application using uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Docker

This application is containerized and available as a Docker image for easy deployment.

### Prerequisites

- Docker 25+ installed and running
- Docker Compose plugin installed
- Docker Hub account (for pulling/pushing images)

### Building the Image

Build the Docker image locally:

```bash
docker build -t devops-info-service:latest .
```

Tag for your Docker Hub repository:

```bash
docker tag devops-info-service:latest <your-dockerhub-username>/devops-info-service:latest
```

### Running the Container

Run the container with default settings:

```bash
docker run -d -p 8000:8000 --name devops-service devops-info-service:latest
```

Run with custom environment variables:

```bash
docker run -d -p 8080:8080 \
  -e PORT=8080 \
  -e DEBUG=true \
  -e VISITS_FILE=/data/visits \
  -v $(pwd)/data:/data \
  --name devops-service \
  devops-info-service:latest
```

### Local Persistence Test with Docker Compose

A local [`docker-compose.yml`](app_python/docker-compose.yml) is included for Lab 12.

Start the service:

```bash
docker compose up --build -d
```

Generate visits and inspect the persisted file:

```bash
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/visits
cat ./data/visits
```

Restart the container and verify the counter is preserved:

```bash
docker compose restart
curl http://localhost:8000/visits
```

Stop the stack:

```bash
docker compose down
```

### Pulling from Docker Hub

Pull and run the pre-built image:

```bash
docker pull netimaaaa/devops-info-service:latest
docker run -d -p 8000:8000 --name devops-service netimaaaa/devops-info-service:latest
```

### Container Management

```bash
# View running containers
docker ps

# View container logs
docker logs devops-service

# Stop the container
docker stop devops-service

# Remove the container
docker rm devops-service

# View image details
docker images devops-info-service
```

### Testing the Containerized Application

Once the container is running, test the endpoints:

```bash
# Test main endpoint
curl http://localhost:8000/

# Test visits endpoint
curl http://localhost:8000/visits

# Test health check
curl http://localhost:8000/health
```

## API Endpoints

### GET /

Returns comprehensive service and system information and increments the persisted visits counter.

**Response Example:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Darwin",
    "platform_version": "Darwin Kernel Version 23.0.0",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.11.5"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hours, 0 minutes",
    "current_time": "2026-01-26T18:00:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.1.2",
    "method": "GET",
    "path": "/"
  },
  "visits": {
    "count": 3,
    "file": "./data/visits"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information and increment visits counter"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    },
    {
      "path": "/visits",
      "method": "GET",
      "description": "Current persisted visits counter"
    }
  ]
}
```

**Testing:**
```bash
curl http://localhost:8000/
curl http://localhost:8000/ | jq
http http://localhost:8000/
```

### GET /visits

Returns the current persisted visits counter without incrementing it.

**Response Example:**
```json
{
  "visits": 3,
  "file": "./data/visits"
}
```

**Testing:**
```bash
curl http://localhost:8000/visits
```

### GET /health

Simple health check endpoint for monitoring and orchestration tools.

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T18:00:00.000000+00:00",
  "uptime_seconds": 3600
}
```

**Testing:**
```bash
curl http://localhost:8000/health
```

**HTTP Status Codes:**
- `200 OK`: Service is healthy and operational

## Configuration

The application supports the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind to |
| `PORT` | `8000` | Port number to listen on |
| `DEBUG` | `false` | Enable debug mode and auto-reload |
| `VISITS_FILE` | `./data/visits` | Path to the persisted visits counter file |

## Testing

Run the automated test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=.
```

## Project Structure

```text
app_python/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── README.md
├── requirements.txt
├── data/
└── tests/
```

## Notes for Kubernetes

For Lab 12, the application is designed to:
- Read configuration from mounted ConfigMaps and environment variables
- Store the visits counter on a mounted persistent volume
- Use `VISITS_FILE=/data/visits` inside the container

## License

This project is created for educational purposes as part of the DevOps Core Course.

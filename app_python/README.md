# DevOps Info Service

A production-ready Python web service that provides comprehensive system information and health status monitoring. Built with FastAPI for the DevOps Core Course.

## Overview

This service reports detailed information about itself and its runtime environment, including:
- Service metadata (name, version, framework)
- System information (hostname, platform, architecture, CPU count)
- Runtime statistics (uptime, current time, timezone)
- Request details (client IP, user agent, HTTP method)
- Available API endpoints

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

### Custom Configuration

Use environment variables to customize the service:

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
```

### Using Uvicorn Directly

You can also run the application using uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### GET /

Returns comprehensive service and system information.

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
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    }
  ]
}
```

**Testing:**
```bash
# Using curl
curl http://localhost:8000/

# Using curl with pretty print
curl http://localhost:8000/ | jq

# Using HTTPie
http http://localhost:8000/
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

**Example:**
```bash
export HOST=127.0.0.1
export PORT=8080
export DEBUG=true
python app.py
```

## Development

### Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── .gitignore               # Git ignore patterns
├── README.md                # This file
├── tests/                   # Unit tests (Lab 3)
│   └── __init__.py
└── docs/                    # Lab documentation
    ├── LAB01.md            # Lab submission
    └── screenshots/        # Proof of work
```

### Code Quality

The application follows Python best practices:
- **PEP 8** style guide compliance
- **Type hints** for better code clarity
- **Docstrings** for all functions
- **Logging** for debugging and monitoring
- **Error handling** for robustness

### Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Port Already in Use

If you see "Address already in use" error:
```bash
# Find process using the port
lsof -i :8000

# Kill the process or use a different port
PORT=8080 python app.py
```

### Module Not Found

Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Permission Denied

On Unix systems, ports below 1024 require root privileges:
```bash
# Use a port above 1024
PORT=8000 python app.py

# Or run with sudo (not recommended)
sudo python app.py
```

## Future Enhancements

This service will evolve throughout the DevOps course:
- **Lab 2**: Docker containerization with multi-stage builds
- **Lab 3**: Unit tests and CI/CD pipeline
- **Lab 8**: Prometheus metrics endpoint
- **Lab 9**: Kubernetes deployment with health probes
- **Lab 12**: Persistent storage for visit counter
- **Lab 13**: Multi-environment deployment with GitOps

## License

This project is part of the DevOps Core Course.

## Author

Created for Lab 01 - DevOps Info Service: Web Application Development
"""
DevOps Info Service
Main application module using FastAPI
"""
import os
import socket
import platform
import json
from datetime import datetime, timezone
from typing import Dict, List, Any
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


# --- Prometheus metrics ---
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

endpoint_calls_total = Counter(
    'devops_info_endpoint_calls_total',
    'Total calls per named endpoint',
    ['endpoint']
)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'path'):
            log_data['path'] = record.path
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


# Configure JSON logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Also configure root logger for uvicorn
root_logger = logging.getLogger()
root_logger.handlers = []
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

app = FastAPI(
    title="DevOps Info Service",
    description="DevOps course info service",
    version="1.0.0"
)

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

START_TIME = datetime.now(timezone.utc)


def get_system_info() -> Dict[str, Any]:
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


def get_uptime() -> Dict[str, Any]:
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_request_info(request: Request) -> Dict[str, str]:
    """Extract request information."""
    return {
        'client_ip': request.client.host if request.client else 'unknown',
        'user_agent': request.headers.get('user-agent', 'unknown'),
        'method': request.method,
        'path': request.url.path
    }


def get_endpoints() -> List[Dict[str, str]]:
    """List available endpoints."""
    return [
        {
            'path': '/',
            'method': 'GET',
            'description': 'Service information'
        },
        {
            'path': '/health',
            'method': 'GET',
            'description': 'Health check'
        }
    ]


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all HTTP requests and record Prometheus metrics."""
    # Normalize endpoint label (avoid high cardinality from dynamic paths)
    endpoint = request.url.path

    http_requests_in_progress.inc()
    start_time = datetime.now(timezone.utc)

    try:
        response = await call_next(request)
    finally:
        http_requests_in_progress.dec()

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code)
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)

    logger.info(
        f"HTTP {request.method} {request.url.path} - {response.status_code}",
        extra={
            'method': request.method,
            'path': str(request.url.path),
            'status_code': response.status_code,
            'client_ip': request.client.host if request.client else 'unknown',
            'duration_seconds': duration
        }
    )

    return response


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def index(request: Request) -> Dict[str, Any]:
    """Main endpoint - service and system information."""
    endpoint_calls_total.labels(endpoint='/').inc()
    uptime = get_uptime()
    
    return {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'FastAPI'
        },
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': get_request_info(request),
        'endpoints': get_endpoints()
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    endpoint_calls_total.labels(endpoint='/health').inc()
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist'
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 500 errors."""
    logger.error(
        f"Internal server error: {str(exc)}",
        extra={
            'method': request.method,
            'path': str(request.url.path),
            'client_ip': request.client.host if request.client else 'unknown'
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        f"Starting DevOps Info Service",
        extra={
            'host': HOST,
            'port': PORT,
            'debug': DEBUG
        }
    )
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=False,
        log_level="debug" if DEBUG else "info"
    )
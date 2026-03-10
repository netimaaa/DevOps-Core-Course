"""
DevOps Info Service
Main application module using FastAPI
"""
import os
import socket
import platform
from datetime import datetime, timezone
from typing import Dict, List, Any
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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


@app.get("/")
async def index(request: Request) -> Dict[str, Any]:
    """Main endpoint - service and system information."""
    logger.info(f"Request: {request.method} {request.url.path}")
    
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
    logger.debug("Health check requested")
    
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
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )
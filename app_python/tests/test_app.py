"""
Unit tests for DevOps Info Service
Testing framework: pytest
"""
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from app import app, get_endpoints, get_system_info, get_uptime


@pytest.fixture(autouse=True)
def reset_visits_file():
    """Use isolated visits file for each test."""
    with tempfile.TemporaryDirectory() as temp_dir:
        visits_file = Path(temp_dir) / 'visits'
        app_module.VISITS_FILE = visits_file
        app_module.VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
        app_module.write_visits_count(0)
        yield


@pytest.fixture()
def client():
    """Create test client with startup events."""
    with TestClient(app) as test_client:
        yield test_client


class TestMainEndpoint:
    """Tests for GET / endpoint"""

    def test_main_endpoint_status_code(self, client):
        """Test that main endpoint returns 200 OK"""
        response = client.get("/")
        assert response.status_code == 200

    def test_main_endpoint_json_structure(self, client):
        """Test that response has correct JSON structure"""
        response = client.get("/")
        data = response.json()

        # Check top-level keys
        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "request" in data
        assert "visits" in data
        assert "endpoints" in data

    def test_service_information(self, client):
        """Test service metadata fields"""
        response = client.get("/")
        service = response.json()["service"]

        assert service["name"] == "devops-info-service"
        assert service["version"] == "1.0.0"
        assert service["description"] == "DevOps course info service"
        assert service["framework"] == "FastAPI"

    def test_system_information_fields(self, client):
        """Test that system info contains required fields"""
        response = client.get("/")
        system = response.json()["system"]

        assert "hostname" in system
        assert "platform" in system
        assert "platform_version" in system
        assert "architecture" in system
        assert "cpu_count" in system
        assert "python_version" in system

        # Verify types
        assert isinstance(system["hostname"], str)
        assert isinstance(system["platform"], str)
        assert isinstance(system["cpu_count"], int)

    def test_runtime_information(self, client):
        """Test runtime statistics"""
        response = client.get("/")
        runtime = response.json()["runtime"]

        assert "uptime_seconds" in runtime
        assert "uptime_human" in runtime
        assert "current_time" in runtime
        assert "timezone" in runtime

        # Verify types
        assert isinstance(runtime["uptime_seconds"], int)
        assert isinstance(runtime["uptime_human"], str)
        assert runtime["timezone"] == "UTC"

        # Verify uptime is non-negative
        assert runtime["uptime_seconds"] >= 0

    def test_request_information(self, client):
        """Test request details are captured"""
        response = client.get("/")
        request_info = response.json()["request"]

        assert "client_ip" in request_info
        assert "user_agent" in request_info
        assert "method" in request_info
        assert "path" in request_info

        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"

    def test_endpoints_list(self, client):
        """Test that endpoints list is provided"""
        response = client.get("/")
        endpoints = response.json()["endpoints"]

        assert isinstance(endpoints, list)
        assert len(endpoints) >= 3

        # Check endpoint structure
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint

    def test_root_endpoint_increments_visits_counter(self, client):
        """Test that root endpoint increments persisted visits counter."""
        first_response = client.get("/")
        second_response = client.get("/")

        assert first_response.json()["visits"]["count"] == 1
        assert second_response.json()["visits"]["count"] == 2

    def test_visits_file_is_updated(self, client):
        """Test that visits counter is stored in file."""
        client.get("/")
        assert app_module.VISITS_FILE.read_text(encoding='utf-8') == '1'


class TestVisitsEndpoint:
    """Tests for GET /visits endpoint"""

    def test_visits_endpoint_status_code(self, client):
        """Test that visits endpoint returns 200 OK"""
        response = client.get("/visits")
        assert response.status_code == 200

    def test_visits_endpoint_returns_current_count(self, client):
        """Test that visits endpoint returns persisted counter value."""
        client.get("/")
        client.get("/")

        response = client.get("/visits")
        data = response.json()

        assert data["visits"] == 2
        assert data["file"] == str(app_module.VISITS_FILE)


class TestHealthEndpoint:
    """Tests for GET /health endpoint"""

    def test_health_endpoint_status_code(self, client):
        """Test that health endpoint returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_structure(self, client):
        """Test health check response structure"""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data

    def test_health_status_value(self, client):
        """Test that health status is 'healthy'"""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_timestamp_format(self, client):
        """Test that timestamp is in ISO format"""
        response = client.get("/health")
        data = response.json()

        # Verify timestamp can be parsed
        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    def test_health_uptime(self, client):
        """Test that uptime is a non-negative integer"""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0


class TestErrorHandling:
    """Tests for error handling"""

    def test_404_not_found(self, client):
        """Test that non-existent endpoints return 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["error"] == "Not Found"

    def test_404_error_structure(self, client):
        """Test 404 error response structure"""
        response = client.get("/invalid/path")
        data = response.json()

        assert "error" in data
        assert "message" in data
        assert isinstance(data["message"], str)


class TestHelperFunctions:
    """Tests for helper functions"""

    def test_get_system_info(self):
        """Test get_system_info function"""
        info = get_system_info()

        assert isinstance(info, dict)
        assert "hostname" in info
        assert "platform" in info
        assert "cpu_count" in info
        assert "python_version" in info

    def test_get_uptime(self):
        """Test get_uptime function"""
        uptime = get_uptime()

        assert isinstance(uptime, dict)
        assert "seconds" in uptime
        assert "human" in uptime
        assert isinstance(uptime["seconds"], int)
        assert isinstance(uptime["human"], str)
        assert uptime["seconds"] >= 0

    def test_get_endpoints(self):
        """Test get_endpoints function"""
        endpoints = get_endpoints()

        assert isinstance(endpoints, list)
        assert len(endpoints) >= 3

        # Verify structure
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint


class TestResponseHeaders:
    """Tests for HTTP response headers"""

    def test_content_type_json(self, client):
        """Test that responses are JSON"""
        response = client.get("/")
        assert "application/json" in response.headers["content-type"]

    def test_health_content_type(self, client):
        """Test health endpoint content type"""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]


class TestMultipleRequests:
    """Tests for multiple requests behavior"""

    def test_uptime_increases(self, client):
        """Test that uptime increases between requests"""
        response1 = client.get("/health")
        uptime1 = response1.json()["uptime_seconds"]

        time.sleep(1)

        response2 = client.get("/health")
        uptime2 = response2.json()["uptime_seconds"]

        assert uptime2 >= uptime1

    def test_consistent_service_info(self, client):
        """Test that service info remains consistent"""
        response1 = client.get("/")
        response2 = client.get("/")

        service1 = response1.json()["service"]
        service2 = response2.json()["service"]

        assert service1 == service2

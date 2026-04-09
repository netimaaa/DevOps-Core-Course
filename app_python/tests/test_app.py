"""Unit tests for DevOps Info Service."""
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

client = TestClient(app)


class TestIndexEndpoint:
    """Tests for GET / endpoint."""

    def test_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_response_is_json(self):
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_has_service_field(self):
        data = client.get("/").json()
        assert "service" in data

    def test_service_has_required_fields(self):
        service = client.get("/").json()["service"]
        assert "name" in service
        assert "version" in service
        assert "framework" in service

    def test_service_name_value(self):
        service = client.get("/").json()["service"]
        assert service["name"] == "devops-info-service"

    def test_service_framework_value(self):
        service = client.get("/").json()["service"]
        assert service["framework"] == "FastAPI"

    def test_has_system_field(self):
        data = client.get("/").json()
        assert "system" in data

    def test_system_has_hostname(self):
        system = client.get("/").json()["system"]
        assert "hostname" in system
        assert isinstance(system["hostname"], str)
        assert len(system["hostname"]) > 0

    def test_system_has_platform(self):
        system = client.get("/").json()["system"]
        assert "platform" in system

    def test_system_has_python_version(self):
        system = client.get("/").json()["system"]
        assert "python_version" in system
        assert isinstance(system["python_version"], str)

    def test_has_runtime_field(self):
        data = client.get("/").json()
        assert "runtime" in data

    def test_runtime_has_uptime_seconds(self):
        runtime = client.get("/").json()["runtime"]
        assert "uptime_seconds" in runtime
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0

    def test_runtime_has_current_time(self):
        runtime = client.get("/").json()["runtime"]
        assert "current_time" in runtime
        assert isinstance(runtime["current_time"], str)

    def test_has_request_field(self):
        data = client.get("/").json()
        assert "request" in data

    def test_request_has_method(self):
        request_info = client.get("/").json()["request"]
        assert "method" in request_info
        assert request_info["method"] == "GET"

    def test_request_has_path(self):
        request_info = client.get("/").json()["request"]
        assert "path" in request_info
        assert request_info["path"] == "/"

    def test_has_endpoints_field(self):
        data = client.get("/").json()
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) > 0


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_is_json(self):
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_has_status_field(self):
        data = client.get("/health").json()
        assert "status" in data

    def test_status_is_healthy(self):
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_has_timestamp_field(self):
        data = client.get("/health").json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_has_uptime_seconds(self):
        data = client.get("/health").json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0


class TestErrorHandlers:
    """Tests for error handling."""

    def test_404_returns_json(self):
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"] == "Not Found"

    def test_404_has_message(self):
        response = client.get("/nonexistent-path")
        data = response.json()
        assert "message" in data

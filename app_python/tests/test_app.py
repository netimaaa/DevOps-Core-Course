"""
Unit tests for DevOps Info Service
Testing framework: pytest
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, get_system_info, get_uptime, get_endpoints


# Create test client
client = TestClient(app)


class TestMainEndpoint:
    """Tests for GET / endpoint"""
    
    def test_main_endpoint_status_code(self):
        """Test that main endpoint returns 200 OK"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_main_endpoint_json_structure(self):
        """Test that response has correct JSON structure"""
        response = client.get("/")
        data = response.json()
        
        # Check top-level keys
        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "request" in data
        assert "endpoints" in data
    
    def test_service_information(self):
        """Test service metadata fields"""
        response = client.get("/")
        service = response.json()["service"]
        
        assert service["name"] == "devops-info-service"
        assert service["version"] == "1.0.0"
        assert service["description"] == "DevOps course info service"
        assert service["framework"] == "FastAPI"
    
    def test_system_information_fields(self):
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
    
    def test_runtime_information(self):
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
    
    def test_request_information(self):
        """Test request details are captured"""
        response = client.get("/")
        request_info = response.json()["request"]
        
        assert "client_ip" in request_info
        assert "user_agent" in request_info
        assert "method" in request_info
        assert "path" in request_info
        
        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"
    
    def test_endpoints_list(self):
        """Test that endpoints list is provided"""
        response = client.get("/")
        endpoints = response.json()["endpoints"]
        
        assert isinstance(endpoints, list)
        assert len(endpoints) >= 2
        
        # Check endpoint structure
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint


class TestHealthEndpoint:
    """Tests for GET /health endpoint"""
    
    def test_health_endpoint_status_code(self):
        """Test that health endpoint returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_endpoint_structure(self):
        """Test health check response structure"""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
    
    def test_health_status_value(self):
        """Test that health status is 'healthy'"""
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
    
    def test_health_timestamp_format(self):
        """Test that timestamp is in ISO format"""
        response = client.get("/health")
        data = response.json()
        
        # Verify timestamp can be parsed
        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        # Should be parseable as ISO format
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    def test_health_uptime(self):
        """Test that uptime is a non-negative integer"""
        response = client.get("/health")
        data = response.json()
        
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_not_found(self):
        """Test that non-existent endpoints return 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert data["error"] == "Not Found"
    
    def test_404_error_structure(self):
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
        assert len(endpoints) >= 2
        
        # Verify structure
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint


class TestResponseHeaders:
    """Tests for HTTP response headers"""
    
    def test_content_type_json(self):
        """Test that responses are JSON"""
        response = client.get("/")
        assert "application/json" in response.headers["content-type"]
    
    def test_health_content_type(self):
        """Test health endpoint content type"""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]


class TestMultipleRequests:
    """Tests for multiple requests behavior"""
    
    def test_uptime_increases(self):
        """Test that uptime increases between requests"""
        import time
        
        response1 = client.get("/health")
        uptime1 = response1.json()["uptime_seconds"]
        
        time.sleep(1)
        
        response2 = client.get("/health")
        uptime2 = response2.json()["uptime_seconds"]
        
        assert uptime2 >= uptime1
    
    def test_consistent_service_info(self):
        """Test that service info remains consistent"""
        response1 = client.get("/")
        response2 = client.get("/")
        
        service1 = response1.json()["service"]
        service2 = response2.json()["service"]
        
        assert service1 == service2


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_empty_path_redirects_to_root(self):
        """Test that empty path works"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_trailing_slash_health(self):
        """Test health endpoint with trailing slash"""
        response = client.get("/health/")
        # FastAPI redirects or handles this
        assert response.status_code in [200, 307, 404]
    
    def test_case_sensitive_paths(self):
        """Test that paths are case-sensitive"""
        response = client.get("/Health")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test POST on GET-only endpoint"""
        response = client.post("/")
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
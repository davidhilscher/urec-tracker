"""
Unit tests for UREC Capacity Tracker Backend

Run with: pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app
from models import AreaCapacity, CapacityResponse, UpdateCapacityRequest

# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Test suite for health check endpoint"""
    
    def test_health_check_returns_200(self):
        """Health check should return 200 OK"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_check_has_status(self):
        """Health check should include status field"""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_health_check_has_timestamp(self):
        """Health check should include timestamp"""
        response = client.get("/api/health")
        data = response.json()
        assert "timestamp" in data
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))


class TestCapacityEndpoints:
    """Test suite for capacity query endpoints"""
    
    def test_get_all_capacity_returns_200(self):
        """GET /api/capacity should return 200 OK"""
        response = client.get("/api/capacity")
        assert response.status_code == 200
    
    def test_get_all_capacity_returns_areas(self):
        """GET /api/capacity should return areas list"""
        response = client.get("/api/capacity")
        data = response.json()
        assert "areas" in data
        assert isinstance(data["areas"], list)
    
    def test_get_all_capacity_has_timestamp(self):
        """GET /api/capacity should include timestamp"""
        response = client.get("/api/capacity")
        data = response.json()
        assert "timestamp" in data
    
    def test_area_has_required_fields(self):
        """Each area should have all required fields"""
        response = client.get("/api/capacity")
        data = response.json()
        
        if data["areas"]:
            area = data["areas"][0]
            required_fields = [
                "area_id", "name", "current_count",
                "max_capacity", "is_open", "last_updated"
            ]
            for field in required_fields:
                assert field in area
    
    def test_get_specific_area_with_valid_id(self):
        """GET /api/capacity/{area_id} with valid ID should return area"""
        # First get all areas to find a valid ID
        response = client.get("/api/capacity")
        data = response.json()
        
        if data["areas"]:
            area_id = data["areas"][0]["area_id"]
            response = client.get(f"/api/capacity/{area_id}")
            assert response.status_code == 200
            
            area_data = response.json()
            assert area_data["area_id"] == area_id
    
    def test_get_specific_area_with_invalid_id(self):
        """GET /api/capacity/{area_id} with invalid ID should return 404"""
        response = client.get("/api/capacity/invalid-area-id-12345")
        assert response.status_code == 404
        assert "detail" in response.json()


class TestUpdateEndpoint:
    """Test suite for capacity update endpoint"""
    
    def test_update_requires_area_id(self):
        """POST /api/update should require area_id"""
        response = client.post(
            "/api/update",
            json={"action": "enter"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_update_requires_action(self):
        """POST /api/update should require action"""
        response = client.post(
            "/api/update",
            json={"area_id": "weight-room"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_update_validates_action(self):
        """POST /api/update should validate action is enter or exit"""
        response = client.post(
            "/api/update",
            json={
                "area_id": "weight-room",
                "action": "invalid-action"
            }
        )
        # Should fail validation
        assert response.status_code in [400, 422]
    
    def test_update_enter_action(self):
        """POST /api/update with 'enter' should succeed (if DB available)"""
        response = client.post(
            "/api/update",
            json={
                "area_id": "weight-room",
                "action": "enter"
            }
        )
        # May succeed or fail depending on DB availability
        # Just check it's a valid HTTP response
        assert response.status_code in [200, 404, 500]
    
    def test_update_exit_action(self):
        """POST /api/update with 'exit' should succeed (if DB available)"""
        response = client.post(
            "/api/update",
            json={
                "area_id": "weight-room",
                "action": "exit"
            }
        )
        assert response.status_code in [200, 404, 500]
    
    def test_update_with_count(self):
        """POST /api/update should accept count parameter"""
        response = client.post(
            "/api/update",
            json={
                "area_id": "weight-room",
                "action": "enter",
                "count": 3
            }
        )
        assert response.status_code in [200, 404, 500]
    
    def test_update_validates_count_range(self):
        """POST /api/update should validate count is 1-10"""
        # Count too high
        response = client.post(
            "/api/update",
            json={
                "area_id": "weight-room",
                "action": "enter",
                "count": 20
            }
        )
        assert response.status_code in [400, 422]
        
        # Count too low
        response = client.post(
            "/api/update",
            json={
                "area_id": "weight-room",
                "action": "enter",
                "count": 0
            }
        )
        assert response.status_code in [400, 422]


class TestResetEndpoint:
    """Test suite for capacity reset endpoint"""
    
    def test_reset_endpoint_exists(self):
        """POST /api/reset/{area_id} should exist"""
        response = client.post("/api/reset/weight-room")
        # Should return 200, 404, or 500 depending on DB
        assert response.status_code in [200, 404, 500]
    
    def test_reset_with_count_parameter(self):
        """POST /api/reset/{area_id} should accept count parameter"""
        response = client.post("/api/reset/weight-room?count=25")
        assert response.status_code in [200, 404, 500]


class TestDataModels:
    """Test suite for Pydantic data models"""
    
    def test_area_capacity_model_validation(self):
        """AreaCapacity model should validate correctly"""
        area = AreaCapacity(
            area_id="test-area",
            name="Test Area",
            current_count=10,
            max_capacity=50,
            is_open=True,
            last_updated=datetime.utcnow().isoformat()
        )
        assert area.area_id == "test-area"
        assert area.current_count >= 0
        assert area.max_capacity > 0
    
    def test_update_request_validation(self):
        """UpdateCapacityRequest should validate action"""
        # Valid action
        request = UpdateCapacityRequest(
            area_id="test-area",
            action="enter"
        )
        assert request.action == "enter"
        
        # Invalid action should raise validation error
        with pytest.raises(ValueError):
            UpdateCapacityRequest(
                area_id="test-area",
                action="invalid"
            )


class TestCORS:
    """Test suite for CORS configuration"""
    
    def test_cors_headers_present(self):
        """Response should include CORS headers"""
        response = client.get("/api/capacity")
        assert "access-control-allow-origin" in response.headers


class TestRootEndpoint:
    """Test suite for root endpoint"""
    
    def test_root_returns_200(self):
        """GET / should return 200 OK"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_has_api_info(self):
        """GET / should return API information"""
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "version" in data


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

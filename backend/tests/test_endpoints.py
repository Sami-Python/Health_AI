import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Verify path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock
# Mock firestore_manager BEFORE importing main to avoid initialization error
mock_firestore_manager = MagicMock()
sys.modules["firestore_manager"] = mock_firestore_manager

from main import app
from auth_middleware import verify_token

client = TestClient(app)

# Mock Auth Dependency
def mock_auth_dependency():
    return {"uid": "test_user_123", "email": "test@example.com"}

# Apply override
app.dependency_overrides[verify_token] = mock_auth_dependency

def test_create_goal_success():
    """Test successful goal creation."""
    payload = {
        "activity_type": "Running",
        "target_value": 42.2,
        "target_unit": "km",
        "period_type": "target_date",
        "target_date": "2026-07-01",
        "frequency": "Monthly",
        "description": "Marathon prep"
    }

    # Since we mocked the module, we need to configure the mock function return value on the module mock
    mock_firestore_manager.add_goal.return_value = True

    response = client.post("/goals", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Goal added"}
    
    # Verify add_goal was called
    mock_firestore_manager.add_goal.assert_called_once()
    call_args = mock_firestore_manager.add_goal.call_args
    assert call_args[0][0] == "test_user_123"
    assert call_args[0][1]['activity_type'] == "Running"
    assert call_args[0][1]['target_value'] == 42.2

def test_create_goal_validation_error():
    """Test validation error (missing field)."""
    payload = {
        "activity_type": "Running",
        # Missing target_value
        "target_unit": "km",
        "frequency": "Weekly"
    }

    response = client.post("/goals", json=payload)
    assert response.status_code == 422 # Unprocessable Entity

def test_create_goal_db_failure():
    """Test handling of database failure."""
    payload = {
        "activity_type": "Running",
        "target_value": 10,
        "target_unit": "km",
        "period_type": "weekly",
        "frequency": "Weekly"
    }

    mock_firestore_manager.add_goal.return_value = False

    response = client.post("/goals", json=payload)
    assert response.status_code == 500

def test_get_readiness():
    """Test get_readiness endpoint."""
    mock_firestore_manager.get_latest_readiness.return_value = {"readiness": 85, "date": "2026-01-05"}
    
    response = client.get("/readiness")
    assert response.status_code == 200
    assert response.json() == {"readiness": 85, "date": "2026-01-05"}
    mock_firestore_manager.get_latest_readiness.assert_called_once()

def test_get_next_workout_found():
    """Test get_next_workout endpoint with data."""
    mock_firestore_manager.get_next_workout.return_value = {"content": {"activity": "Run"}, "date": "2026-01-06"}
    
    response = client.get("/next-workout")
    assert response.status_code == 200
    assert response.json() == {"content": {"activity": "Run"}, "date": "2026-01-06"}
    mock_firestore_manager.get_next_workout.assert_called_once()

def test_get_next_workout_empty():
    """Test get_next_workout endpoint when no data."""
    mock_firestore_manager.get_next_workout.return_value = None
    
    response = client.get("/next-workout")
    assert response.status_code == 200
    assert response.json() == {}

def test_get_weekly_status():
    """Test get_weekly_status endpoint aggregation."""
    mock_firestore_manager.get_weekly_load_status.return_value = (500, 600, {})
    
    response = client.get("/workouts/weekly-status")
    assert response.status_code == 200
    assert response.json() == {
        "current_load": 500,
        "planned_load": 600,
        "breakdown": {}
    }
    mock_firestore_manager.get_weekly_load_status.assert_called_once_with("test_user_123")

import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Verify path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Module-level check to avoid crashing if firestore_manager tries to connect on import
# This is still needed if firestore_manager.__init__ does work.
# But for VALIDATING mocks in tests, I will rely on patch('main.db_manager').
if "firestore_manager" not in sys.modules:
    sys.modules["firestore_manager"] = MagicMock()

from main import app
from auth_middleware import verify_token

client = TestClient(app)

# Mock Auth Dependency
def mock_auth_dependency():
    return {"uid": "test_user_123", "email": "test@example.com"}

@pytest.fixture(autouse=True)
def override_auth_dependency():
    """Automatically override auth for all tests in this module."""
    app.dependency_overrides[verify_token] = mock_auth_dependency
    yield
    # Restore original dependency (or clean up)
    app.dependency_overrides = {}

@pytest.fixture
def mock_db():
    """
    Patches 'main.db_manager' so that main.py uses OUR mock.
    Yields the mock object for configuration.
    """
    with patch("main.db_manager") as mock:
        yield mock

def test_create_goal_success(mock_db):
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

    mock_db.add_goal.return_value = True

    response = client.post("/goals", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Goal added"}
    
    mock_db.add_goal.assert_called_once()
    call_args = mock_db.add_goal.call_args
    # call_args[0] is args, [1] is kwargs. 
    # args: (user_id, goal_data)
    assert call_args[0][0] == "test_user_123"
    assert call_args[0][1]['activity_type'] == "Running"

def test_create_goal_validation_error(mock_db):
    """Test validation error (missing field)."""
    payload = {
        "activity_type": "Running",
        # Missing target_value
        "target_unit": "km",
        "frequency": "Weekly"
    }

    response = client.post("/goals", json=payload)
    assert response.status_code == 422 

def test_create_goal_db_failure(mock_db):
    """Test handling of database failure."""
    payload = {
        "activity_type": "Running",
        "target_value": 10,
        "target_unit": "km",
        "period_type": "weekly",
        "frequency": "Weekly"
    }

    mock_db.add_goal.return_value = False

    response = client.post("/goals", json=payload)
    assert response.status_code == 500

def test_get_readiness(mock_db):
    """Test get_readiness endpoint."""
    mock_db.get_latest_readiness.return_value = {"readiness": 85, "date": "2026-01-05"}
    
    response = client.get("/readiness")
    assert response.status_code == 200
    assert response.json() == {"readiness": 85, "date": "2026-01-05"}

def test_get_next_workout_found(mock_db):
    """Test get_next_workout endpoint with data."""
    mock_db.get_next_workout.return_value = {"content": {"activity": "Run"}, "date": "2026-01-06"}
    
    response = client.get("/next-workout")
    assert response.status_code == 200
    assert response.json() == {"content": {"activity": "Run"}, "date": "2026-01-06"}

def test_get_next_workout_empty(mock_db):
    """Test get_next_workout endpoint when no data."""
    mock_db.get_next_workout.return_value = None
    
    response = client.get("/next-workout")
    assert response.status_code == 200
    assert response.json() == {}

def test_get_weekly_status(mock_db):
    """Test get_weekly_status endpoint aggregation."""
    # This was failing with ValueError because mock was polluted.
    # Now patch('main.db_manager') ensures we configure the object main.py actually uses.
    mock_db.get_weekly_load_status.return_value = (500, 600, {})
    
    response = client.get("/workouts/weekly-status")
    
    assert response.status_code == 200
    assert response.json() == {
        "current_load": 500,
        "planned_load": 600,
        "breakdown": {}
    }

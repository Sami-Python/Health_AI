import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock firestore_manager to avoid circular import
if "firestore_manager" not in sys.modules:
    sys.modules["firestore_manager"] = MagicMock()

from main import app
from auth_middleware import verify_token

client = TestClient(app)

# 3. Test Fixtures

@pytest.fixture
def admin_user():
    return {"uid": "admin_123", "email": "admin@example.com"}

@pytest.fixture
def regular_user():
    return {"uid": "user_456", "email": "user@example.com"}

@pytest.fixture
def set_admin_env(monkeypatch):
    """Sets the ADMIN_EMAILS environment variable."""
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com,other@example.com")

# 4. Tests

def test_admin_feedback_access_granted(set_admin_env, admin_user):
    """Test that an admin email can access the endpoint."""
    
    # Mock Auth to return admin user
    app.dependency_overrides[verify_token] = lambda: admin_user
    
    # Mock DB using patch on main.db_manager
    with patch("main.db_manager") as mock_db:
        mock_db.get_all_feedback.return_value = [{"message": "Test feedback"}]
        
        response = client.get("/admin/feedback")
    
    # Cleanup dependency override
    app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert "feedback" in data
    assert data["feedback"][0]["message"] == "Test feedback"

def test_admin_feedback_access_denied(set_admin_env, regular_user):
    """Test that a non-admin email is rejected."""
    
    # Mock Auth to return regular user
    app.dependency_overrides[verify_token] = lambda: regular_user
    
    response = client.get("/admin/feedback")
    
    # Cleanup
    app.dependency_overrides = {}

    assert response.status_code == 403
    assert "detail" in response.json()
    assert response.json()["detail"] == "Admin access denied"

def test_admin_feedback_no_email(set_admin_env):
    """Test user without email (e.g. anonymous provider or error)."""
    
    # User with no email field
    app.dependency_overrides[verify_token] = lambda: {"uid": "anon_123"}
    
    response = client.get("/admin/feedback")
    
    app.dependency_overrides = {}

    assert response.status_code == 403
    assert response.json()["detail"] == "Email required for admin access"

"""
Pytest configuration and shared fixtures for integration tests.

This module provides fixtures for:
- Firebase Emulator connection
- Test user creation and cleanup
- Authenticated test clients
- Test data helpers
"""

import pytest
import os
import time
from typing import Generator, Dict
from fastapi.testclient import TestClient
from firebase_admin import auth, credentials, initialize_app, delete_app
import firebase_admin

# Import main app
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app
import firestore_manager


# ============================================================================
# Session-level Setup
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_firebase_emulator():
    """
    Configure Firebase to use emulator for all tests.
    This runs once per test session.
    """
    # Set emulator environment variables
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
    os.environ["APP_ENV"] = "test"
    
    # Initialize Firebase Admin SDK for emulator
    # Use a dummy project ID for emulator
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF0K0L6oM6KJ3xKLwNXXFPXJVGGNK\n-----END RSA PRIVATE KEY-----",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        initialize_app(cred, {"projectId": "test-project"})
    
    yield
    
    # Cleanup after all tests
    # Note: Emulator data is ephemeral, but we clean up the app
    if firebase_admin._apps:
        delete_app(firebase_admin.get_app())


# ============================================================================
# Test User Fixtures
# ============================================================================

@pytest.fixture
def test_user() -> Generator[Dict[str, str], None, None]:
    """
    Create a test user in Firebase Auth Emulator.
    
    Yields:
        Dict with 'uid', 'email', 'token'
    
    Cleanup:
        Deletes user and all Firestore data after test
    """
    email = f"test_user_{int(time.time())}@test.com"
    password = "test_password_123"
    
    # Create user in Firebase Auth
    user_record = auth.create_user(
        email=email,
        password=password,
        email_verified=True
    )
    
    # Generate custom token for authentication
    custom_token = auth.create_custom_token(user_record.uid)
    
    # Exchange custom token for ID token (simulating client flow)
    # In emulator, we can use the custom token directly as ID token for testing
    id_token = custom_token.decode('utf-8')
    
    user_data = {
        "uid": user_record.uid,
        "email": email,
        "token": id_token,
        "password": password
    }
    
    yield user_data
    
    # Cleanup: Delete all user data from Firestore
    try:
        firestore_manager.delete_all_user_data(user_record.uid)
    except Exception as e:
        print(f"Warning: Failed to clean up Firestore data: {e}")
    
    # Cleanup: Delete user from Firebase Auth
    try:
        auth.delete_user(user_record.uid)
    except Exception as e:
        print(f"Warning: Failed to delete test user: {e}")


@pytest.fixture
def test_admin() -> Generator[Dict[str, str], None, None]:
    """
    Create a test admin user in Firebase Auth Emulator.
    
    Yields:
        Dict with 'uid', 'email', 'token'
    """
    email = "admin@test.com"  # Matches ADMIN_EMAILS in .env.test
    password = "admin_password_123"
    
    # Try to get existing admin user, or create new one
    try:
        user_record = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        user_record = auth.create_user(
            email=email,
            password=password,
            email_verified=True
        )
    
    custom_token = auth.create_custom_token(user_record.uid)
    id_token = custom_token.decode('utf-8')
    
    user_data = {
        "uid": user_record.uid,
        "email": email,
        "token": id_token,
        "password": password
    }
    
    yield user_data
    
    # Note: We don't delete admin user as it might be reused across tests


@pytest.fixture
def second_test_user() -> Generator[Dict[str, str], None, None]:
    """
    Create a second test user for isolation testing.
    
    Yields:
        Dict with 'uid', 'email', 'token'
    """
    email = f"test_user_2_{int(time.time())}@test.com"
    password = "test_password_456"
    
    user_record = auth.create_user(
        email=email,
        password=password,
        email_verified=True
    )
    
    custom_token = auth.create_custom_token(user_record.uid)
    id_token = custom_token.decode('utf-8')
    
    user_data = {
        "uid": user_record.uid,
        "email": email,
        "token": id_token,
        "password": password
    }
    
    yield user_data
    
    # Cleanup
    try:
        firestore_manager.delete_all_user_data(user_record.uid)
        auth.delete_user(user_record.uid)
    except Exception as e:
        print(f"Warning: Failed to clean up second test user: {e}")


# ============================================================================
# Test Client Fixtures
# ============================================================================

@pytest.fixture
def client() -> TestClient:
    """
    Create a FastAPI test client.
    
    Returns:
        TestClient instance
    """
    return TestClient(app)


@pytest.fixture
def authenticated_client(test_user: Dict[str, str]) -> TestClient:
    """
    Create a FastAPI test client with authentication headers.
    
    Args:
        test_user: Test user fixture
    
    Returns:
        TestClient with Authorization header
    """
    client = TestClient(app)
    client.headers = {
        "Authorization": f"Bearer {test_user['token']}"
    }
    return client


@pytest.fixture
def admin_client(test_admin: Dict[str, str]) -> TestClient:
    """
    Create a FastAPI test client with admin authentication.
    
    Args:
        test_admin: Test admin fixture
    
    Returns:
        TestClient with admin Authorization header
    """
    client = TestClient(app)
    client.headers = {
        "Authorization": f"Bearer {test_admin['token']}"
    }
    return client


# ============================================================================
# Helper Fixtures
# ============================================================================

@pytest.fixture
def wait_for_firestore():
    """
    Helper to wait for Firestore writes to complete.
    Firestore has eventual consistency, so we may need to wait.
    """
    def _wait(seconds: float = 0.5):
        time.sleep(seconds)
    return _wait

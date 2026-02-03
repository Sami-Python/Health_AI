"""
Alternative conftest.py for running tests WITHOUT Firebase Emulator.

This version uses a real Firebase test project instead of the emulator.
Use this if you don't want to install Java for the emulator.

IMPORTANT: You need a separate Firebase test project for this approach.
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
# Session-level Setup (Real Firebase Project)
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_firebase_test_project():
    """
    Configure Firebase to use a REAL test project.
    
    REQUIREMENTS:
    1. Create a separate Firebase project for testing
    2. Download service account key
    3. Set FIREBASE_TEST_CREDENTIALS environment variable
    
    Example:
        export FIREBASE_TEST_CREDENTIALS=/path/to/test-service-account.json
    """
    # Check if using emulator or real project
    if os.getenv("USE_FIREBASE_EMULATOR") == "true":
        # Use emulator (requires Java)
        os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
        print("✅ Using Firebase Emulator")
    else:
        # Use real test project
        test_creds = os.getenv("FIREBASE_TEST_CREDENTIALS")
        if not test_creds:
            pytest.skip("FIREBASE_TEST_CREDENTIALS not set. Set it or use emulator.")
        
        print(f"✅ Using real Firebase test project: {test_creds}")
    
    os.environ["APP_ENV"] = "test"
    
    # Initialize Firebase Admin SDK
    if not firebase_admin._apps:
        if os.getenv("USE_FIREBASE_EMULATOR") == "true":
            # Dummy credentials for emulator
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
        else:
            # Real credentials
            cred = credentials.Certificate(os.getenv("FIREBASE_TEST_CREDENTIALS"))
        
        initialize_app(cred)
    
    yield
    
    # Cleanup
    if firebase_admin._apps:
        delete_app(firebase_admin.get_app())


# ============================================================================
# Test User Fixtures (Same as before)
# ============================================================================

@pytest.fixture
def test_user() -> Generator[Dict[str, str], None, None]:
    """Create a test user in Firebase Auth."""
    email = f"test_user_{int(time.time())}@test.com"
    password = "test_password_123"
    
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
        print(f"Warning: Cleanup failed: {e}")


@pytest.fixture
def test_admin() -> Generator[Dict[str, str], None, None]:
    """Create a test admin user."""
    email = "admin@test.com"
    password = "admin_password_123"
    
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


@pytest.fixture
def second_test_user() -> Generator[Dict[str, str], None, None]:
    """Create a second test user for isolation testing."""
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
    
    try:
        firestore_manager.delete_all_user_data(user_record.uid)
        auth.delete_user(user_record.uid)
    except Exception as e:
        print(f"Warning: Cleanup failed: {e}")


# ============================================================================
# Test Client Fixtures (Same as before)
# ============================================================================

@pytest.fixture
def client() -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(test_user: Dict[str, str]) -> TestClient:
    """Create authenticated test client."""
    client = TestClient(app)
    client.headers = {
        "Authorization": f"Bearer {test_user['token']}"
    }
    return client


@pytest.fixture
def admin_client(test_admin: Dict[str, str]) -> TestClient:
    """Create admin test client."""
    client = TestClient(app)
    client.headers = {
        "Authorization": f"Bearer {test_admin['token']}"
    }
    return client


@pytest.fixture
def wait_for_firestore():
    """Helper to wait for Firestore writes."""
    def _wait(seconds: float = 0.5):
        time.sleep(seconds)
    return _wait

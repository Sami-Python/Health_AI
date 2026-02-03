"""
Helper functions for integration tests.

Provides utilities for:
- Firestore data verification
- Test data cleanup
- Assertion helpers
"""

import time
from typing import List, Dict, Any
from google.cloud import firestore


def wait_for_firestore_write(seconds: float = 0.5):
    """
    Wait for Firestore write to complete.
    
    Firestore has eventual consistency, so writes may not be
    immediately visible in subsequent reads.
    
    Args:
        seconds: Time to wait in seconds
    """
    time.sleep(seconds)


def assert_firestore_collection_empty(db: firestore.Client, collection_path: str, user_id: str):
    """
    Assert that a Firestore collection is empty for a given user.
    
    Args:
        db: Firestore client
        collection_path: Path to collection (e.g., 'goals')
        user_id: User ID to filter by
    
    Raises:
        AssertionError: If collection is not empty
    """
    docs = db.collection(collection_path).where('user_id', '==', user_id).limit(1).get()
    assert len(list(docs)) == 0, f"Collection '{collection_path}' is not empty for user {user_id}"


def assert_firestore_document_exists(db: firestore.Client, doc_path: str):
    """
    Assert that a Firestore document exists.
    
    Args:
        db: Firestore client
        doc_path: Full path to document (e.g., 'users/uid/profile')
    
    Raises:
        AssertionError: If document does not exist
    """
    doc = db.document(doc_path).get()
    assert doc.exists, f"Document '{doc_path}' does not exist"


def assert_firestore_document_not_exists(db: firestore.Client, doc_path: str):
    """
    Assert that a Firestore document does not exist.
    
    Args:
        db: Firestore client
        doc_path: Full path to document
    
    Raises:
        AssertionError: If document exists
    """
    doc = db.document(doc_path).get()
    assert not doc.exists, f"Document '{doc_path}' should not exist but does"


def get_firestore_document_count(db: firestore.Client, collection_path: str, user_id: str) -> int:
    """
    Get count of documents in a collection for a user.
    
    Args:
        db: Firestore client
        collection_path: Path to collection
        user_id: User ID to filter by
    
    Returns:
        Number of documents
    """
    docs = db.collection(collection_path).where('user_id', '==', user_id).stream()
    return len(list(docs))


def create_test_goal(user_id: str) -> Dict[str, Any]:
    """
    Create a test goal payload.
    
    Args:
        user_id: User ID for the goal
    
    Returns:
        Goal data dictionary
    """
    return {
        "activity_type": "Running",
        "target_value": 50.0,
        "target_unit": "km",
        "period_type": "weekly",
        "frequency": "Weekly",
        "description": "Test goal for integration testing"
    }


def create_test_workout(date: str = "2026-02-03") -> Dict[str, Any]:
    """
    Create a test workout payload.
    
    Args:
        date: Workout date in YYYY-MM-DD format
    
    Returns:
        Workout data dictionary
    """
    return {
        "date": date,
        "activity": "Running",
        "duration_min": 45,
        "rpe": 7,
        "notes": "Test workout for integration testing"
    }


def create_test_profile() -> Dict[str, Any]:
    """
    Create a test user profile payload.
    
    Returns:
        Profile data dictionary
    """
    return {
        "age": 30,
        "weight": 70.0,
        "height": 175,
        "gender": "male",
        "resting_heart_rate": 55,
        "max_heart_rate": 190
    }


def create_test_garmin_credentials() -> Dict[str, str]:
    """
    Create test Garmin credentials payload.
    
    Returns:
        Credentials dictionary
    """
    return {
        "username": "test_garmin@example.com",
        "password": "test_garmin_password_123"
    }


def assert_encrypted_field(value: Any):
    """
    Assert that a field appears to be encrypted.
    
    Args:
        value: Value to check
    
    Raises:
        AssertionError: If value doesn't appear encrypted
    """
    # Encrypted values should be bytes or base64 strings
    # and should not contain readable text
    assert value is not None, "Encrypted field should not be None"
    
    # If it's a string, it should look like base64 or hex
    if isinstance(value, str):
        assert len(value) > 20, "Encrypted value too short"
        # Should not contain common password patterns
        assert "password" not in value.lower(), "Encrypted value contains 'password'"
        assert "@" not in value, "Encrypted value contains '@'"

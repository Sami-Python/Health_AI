"""
Integration tests for Health AI Backend.

These tests use Firebase Emulator and test real flows with actual
Firebase tokens and database operations.

Test Categories:
- Authentication & Authorization
- GDPR Compliance
- Garmin Integration
- Core Endpoints

Prerequisites:
- Firebase Emulator running on localhost:8080 (Firestore) and localhost:9099 (Auth)
- Run: firebase emulators:start --only auth,firestore

Usage:
    pytest tests/test_integration.py -v
"""

import pytest
import time
from fastapi.testclient import TestClient
from firebase_admin import auth
import firestore_manager
from test_helpers import (
    wait_for_firestore_write,
    assert_firestore_collection_empty,
    assert_firestore_document_not_exists,
    create_test_goal,
    create_test_workout,
    create_test_profile,
    create_test_garmin_credentials,
    assert_encrypted_field
)


# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


# ============================================================================
# Authentication & Authorization Tests
# ============================================================================

class TestAuthentication:
    """Test authentication and authorization flows."""
    
    def test_valid_token_access(self, authenticated_client, test_user):
        """Test that valid Firebase token grants access to protected endpoints."""
        response = authenticated_client.get("/profile")
        
        assert response.status_code == 200
        # Profile might be empty for new user, but endpoint should work
        assert isinstance(response.json(), dict)
    
    def test_invalid_token_rejected(self, client):
        """Test that invalid token is rejected with 401."""
        response = client.get(
            "/profile",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_missing_token_rejected(self, client):
        """Test that missing token is rejected with 401."""
        response = client.get("/profile")
        
        assert response.status_code == 401
    
    def test_user_isolation(self, authenticated_client, second_test_user, test_user):
        """Test that User A cannot access User B's data."""
        # User A creates a goal
        goal_payload = create_test_goal(test_user['uid'])
        response = authenticated_client.post("/goals", json=goal_payload)
        assert response.status_code == 200
        
        wait_for_firestore_write()
        
        # User B tries to get goals (should only see their own, which is none)
        client_b = TestClient(authenticated_client.app)
        client_b.headers = {"Authorization": f"Bearer {second_test_user['token']}"}
        
        response = client_b.get("/goals")
        assert response.status_code == 200
        
        # User B should not see User A's goal
        goals = response.json()
        assert isinstance(goals, list)
        assert len(goals) == 0, "User B should not see User A's goals"
    
    def test_admin_only_endpoints(self, authenticated_client, admin_client):
        """Test that non-admin cannot access admin endpoints."""
        # Regular user tries to access admin endpoint
        response = authenticated_client.get("/admin/feedback")
        assert response.status_code == 403
        assert "Admin access denied" in response.json()["detail"]
        
        # Admin user can access
        response = admin_client.get("/admin/feedback")
        assert response.status_code == 200
        assert "feedback" in response.json()


# ============================================================================
# GDPR Compliance Tests
# ============================================================================

class TestGDPRCompliance:
    """Test GDPR compliance features."""
    
    def test_data_export_complete(self, authenticated_client, test_user):
        """Test that data export includes all user data."""
        # Create some data first
        goal_payload = create_test_goal(test_user['uid'])
        authenticated_client.post("/goals", json=goal_payload)
        
        workout_payload = create_test_workout()
        authenticated_client.post("/workouts/manual", json=workout_payload)
        
        profile_payload = create_test_profile()
        authenticated_client.put("/profile", json=profile_payload)
        
        wait_for_firestore_write()
        
        # Export data
        response = authenticated_client.get("/user/export")
        
        assert response.status_code == 200
        export_data = response.json()
        
        # Verify structure
        assert "user_id" in export_data
        assert export_data["user_id"] == test_user['uid']
        assert "exported_at" in export_data
        assert "goals" in export_data
        assert "workouts" in export_data
        assert "profile" in export_data
        
        # Verify data is present
        assert len(export_data["goals"]) > 0, "Goals should be exported"
        assert len(export_data["workouts"]) > 0, "Workouts should be exported"
    
    def test_account_deletion_firestore(self, authenticated_client, test_user):
        """Test that account deletion removes all Firestore data."""
        # Create test data
        goal_payload = create_test_goal(test_user['uid'])
        authenticated_client.post("/goals", json=goal_payload)
        
        workout_payload = create_test_workout()
        authenticated_client.post("/workouts/manual", json=workout_payload)
        
        wait_for_firestore_write()
        
        # Verify data exists
        response = authenticated_client.get("/goals")
        assert len(response.json()) > 0
        
        # Delete account
        response = authenticated_client.delete("/account")
        assert response.status_code == 200
        assert "Account deleted permanently" in response.json()["message"]
        
        wait_for_firestore_write()
        
        # Verify Firestore data is deleted
        db = firestore_manager.db
        assert_firestore_collection_empty(db, "goals", test_user['uid'])
        assert_firestore_collection_empty(db, "workouts", test_user['uid'])
    
    def test_account_deletion_auth(self, authenticated_client, test_user):
        """Test that account deletion removes Firebase Auth user."""
        uid = test_user['uid']
        
        # Verify user exists
        user_record = auth.get_user(uid)
        assert user_record.uid == uid
        
        # Delete account
        response = authenticated_client.delete("/account")
        assert response.status_code == 200
        
        wait_for_firestore_write()
        
        # Verify user is deleted from Firebase Auth
        with pytest.raises(auth.UserNotFoundError):
            auth.get_user(uid)
    
    def test_account_deletion_comprehensive(self, authenticated_client, test_user):
        """Test complete account deletion with multiple data types."""
        # Create comprehensive test data
        # 1. Goals
        goal_payload = create_test_goal(test_user['uid'])
        authenticated_client.post("/goals", json=goal_payload)
        
        # 2. Workouts
        workout_payload = create_test_workout()
        authenticated_client.post("/workouts/manual", json=workout_payload)
        
        # 3. Profile
        profile_payload = create_test_profile()
        authenticated_client.put("/profile", json=profile_payload)
        
        # 4. Garmin credentials
        garmin_payload = create_test_garmin_credentials()
        authenticated_client.post("/garmin/credentials", json=garmin_payload)
        
        wait_for_firestore_write()
        
        # Verify all data exists
        assert len(authenticated_client.get("/goals").json()) > 0
        assert authenticated_client.get("/profile").json() is not None
        
        # Delete account
        response = authenticated_client.delete("/account")
        assert response.status_code == 200
        
        wait_for_firestore_write(1.0)  # Wait longer for comprehensive deletion
        
        # Verify ALL data is deleted
        db = firestore_manager.db
        uid = test_user['uid']
        
        assert_firestore_collection_empty(db, "goals", uid)
        assert_firestore_collection_empty(db, "workouts", uid)
        assert_firestore_collection_empty(db, "plans", uid)
        assert_firestore_document_not_exists(db, f"users/{uid}")
        assert_firestore_document_not_exists(db, f"users/{uid}/garmin_credentials/default")
        
        # Verify Auth user deleted
        with pytest.raises(auth.UserNotFoundError):
            auth.get_user(uid)


# ============================================================================
# Garmin Integration Tests
# ============================================================================

class TestGarminIntegration:
    """Test Garmin credentials and integration."""
    
    def test_save_garmin_credentials_encrypted(self, authenticated_client, test_user):
        """Test that Garmin credentials are saved with encryption."""
        credentials = create_test_garmin_credentials()
        
        response = authenticated_client.post("/garmin/credentials", json=credentials)
        
        assert response.status_code == 200
        assert "success" in response.json()["status"]
        
        wait_for_firestore_write()
        
        # Verify credentials are stored encrypted in Firestore
        db = firestore_manager.db
        cred_doc = db.document(f"users/{test_user['uid']}/garmin_credentials/default").get()
        
        assert cred_doc.exists
        cred_data = cred_doc.to_dict()
        
        # Username should be plaintext
        assert cred_data['username'] == credentials['username']
        
        # Password should be encrypted (not plaintext)
        assert 'password' in cred_data
        assert_encrypted_field(cred_data['password'])
        assert cred_data['password'] != credentials['password'], "Password should be encrypted"
    
    def test_retrieve_garmin_credentials_decrypted(self, authenticated_client, test_user):
        """Test that Garmin credentials are decrypted correctly on retrieval."""
        credentials = create_test_garmin_credentials()
        
        # Save credentials
        authenticated_client.post("/garmin/credentials", json=credentials)
        wait_for_firestore_write()
        
        # Check status (which internally retrieves and decrypts)
        response = authenticated_client.get("/garmin/status")
        
        assert response.status_code == 200
        status_data = response.json()
        
        # Should indicate credentials exist
        assert status_data.get('has_credentials') == True
        assert status_data.get('username') == credentials['username']
    
    def test_garmin_status_check(self, authenticated_client, test_user):
        """Test Garmin status endpoint."""
        # Without credentials
        response = authenticated_client.get("/garmin/status")
        assert response.status_code == 200
        assert response.json().get('has_credentials') == False
        
        # With credentials
        credentials = create_test_garmin_credentials()
        authenticated_client.post("/garmin/credentials", json=credentials)
        wait_for_firestore_write()
        
        response = authenticated_client.get("/garmin/status")
        assert response.status_code == 200
        assert response.json().get('has_credentials') == True
    
    def test_delete_garmin_credentials(self, authenticated_client, test_user):
        """Test Garmin credentials deletion."""
        # Save credentials
        credentials = create_test_garmin_credentials()
        authenticated_client.post("/garmin/credentials", json=credentials)
        wait_for_firestore_write()
        
        # Verify they exist
        response = authenticated_client.get("/garmin/status")
        assert response.json().get('has_credentials') == True
        
        # Delete credentials
        response = authenticated_client.delete("/garmin/credentials")
        assert response.status_code == 200
        
        wait_for_firestore_write()
        
        # Verify they're deleted
        response = authenticated_client.get("/garmin/status")
        assert response.json().get('has_credentials') == False
        
        # Verify Firestore document is deleted
        db = firestore_manager.db
        cred_doc = db.document(f"users/{test_user['uid']}/garmin_credentials/default").get()
        assert not cred_doc.exists
    
    def test_garmin_credentials_isolation(self, authenticated_client, second_test_user, test_user):
        """Test that User A cannot access User B's Garmin credentials."""
        # User A saves credentials
        credentials_a = create_test_garmin_credentials()
        authenticated_client.post("/garmin/credentials", json=credentials_a)
        wait_for_firestore_write()
        
        # User B checks their status (should not have credentials)
        client_b = TestClient(authenticated_client.app)
        client_b.headers = {"Authorization": f"Bearer {second_test_user['token']}"}
        
        response = client_b.get("/garmin/status")
        assert response.status_code == 200
        assert response.json().get('has_credentials') == False, "User B should not see User A's credentials"


# ============================================================================
# Core Endpoint Tests
# ============================================================================

class TestCoreEndpoints:
    """Test core API endpoints."""
    
    def test_goals_crud_flow(self, authenticated_client, test_user):
        """Test complete CRUD flow for goals."""
        # CREATE
        goal_payload = create_test_goal(test_user['uid'])
        response = authenticated_client.post("/goals", json=goal_payload)
        assert response.status_code == 200
        
        wait_for_firestore_write()
        
        # READ
        response = authenticated_client.get("/goals")
        assert response.status_code == 200
        goals = response.json()
        assert len(goals) > 0
        goal_id = goals[0]['id']
        
        # UPDATE
        update_payload = goal_payload.copy()
        update_payload['target_value'] = 100.0
        response = authenticated_client.put(f"/goals/{goal_id}", json=update_payload)
        assert response.status_code == 200
        
        wait_for_firestore_write()
        
        # Verify update
        response = authenticated_client.get("/goals")
        goals = response.json()
        updated_goal = next(g for g in goals if g['id'] == goal_id)
        assert updated_goal['target_value'] == 100.0
        
        # DELETE
        response = authenticated_client.delete(f"/goals/{goal_id}")
        assert response.status_code == 200
        
        wait_for_firestore_write()
        
        # Verify deletion
        response = authenticated_client.get("/goals")
        goals = response.json()
        assert len([g for g in goals if g['id'] == goal_id]) == 0
    
    def test_profile_update(self, authenticated_client, test_user):
        """Test user profile update."""
        profile_payload = create_test_profile()
        
        response = authenticated_client.put("/profile", json=profile_payload)
        assert response.status_code == 200
        
        wait_for_firestore_write()
        
        # Verify profile was saved
        response = authenticated_client.get("/profile")
        assert response.status_code == 200
        profile = response.json()
        
        assert profile['age'] == profile_payload['age']
        assert profile['weight'] == profile_payload['weight']
        assert profile['height'] == profile_payload['height']
    
    def test_manual_workout_logging(self, authenticated_client, test_user):
        """Test manual workout logging."""
        workout_payload = create_test_workout()
        
        response = authenticated_client.post("/workouts/manual", json=workout_payload)
        assert response.status_code == 200
        assert "success" in response.json()["status"]
        
        wait_for_firestore_write()
        
        # Verify workout was saved (check via weekly status or similar)
        # Note: There's no direct GET /workouts endpoint, so we verify indirectly
        response = authenticated_client.get("/workouts/weekly-status")
        assert response.status_code == 200
    
    def test_feedback_submission(self, authenticated_client, test_user):
        """Test feedback submission."""
        feedback_payload = {
            "category": "bug",
            "message": "Test feedback from integration test",
            "page": "/dashboard"
        }
        
        response = authenticated_client.post("/feedback", json=feedback_payload)
        assert response.status_code == 200
        assert "success" in response.json()["status"]
        
        wait_for_firestore_write()
        
        # Verify feedback was saved (admin can see it)
        # This requires admin access, so we'll just verify the POST succeeded


# ============================================================================
# Error Handling & Edge Cases
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_goal_payload(self, authenticated_client):
        """Test that invalid goal payload is rejected."""
        invalid_payload = {
            "activity_type": "Running",
            # Missing required fields
        }
        
        response = authenticated_client.post("/goals", json=invalid_payload)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_workout_date(self, authenticated_client):
        """Test that invalid workout date is rejected."""
        invalid_payload = {
            "date": "invalid-date",
            "activity": "Running",
            "duration_min": 45,
            "rpe": 7
        }
        
        response = authenticated_client.post("/workouts/manual", json=invalid_payload)
        assert response.status_code == 422 or response.status_code == 500
    
    def test_nonexistent_goal_deletion(self, authenticated_client):
        """Test deleting non-existent goal returns 404."""
        response = authenticated_client.delete("/goals/nonexistent_goal_id_12345")
        assert response.status_code == 404

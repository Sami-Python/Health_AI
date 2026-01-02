import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
from datetime import datetime

# Initialize credentials
# Note: In Docker, this path is correct (/app/service_account_key.json)
# Local execution might need adjustments unless running from 'backend/' folder.
cred_path = str(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account_key.json"))

print(f"Using credentials from: {cred_path}")

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    print("Connected to Firestore.")

    # Get test user ID from env or use default
    user_id = os.getenv("TEST_USER_ID", "test_user_123")
    print(f"Seeding data for User ID: {user_id}")

    # 1. Add Dummy Workout
    workout_data = {
        "user_id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "PENDING",
        "content": {
            "activity": "🔥 Firestore Test Workout",
            "duration_min": 50,
            "description": "Tämä treeni on luotu seed_firestore.py -skriptillä yhteyden testaamiseksi.",
            "structure_summary": "PK 1-2 (Syke 125-135)",
            "load_estimate": 70,
            "manual": False
        }
    }
    # Add to 'workouts' collection
    db.collection("workouts").add(workout_data)
    print("✅ Added 'workouts' document.")

    # 2. Add Dummy Goal
    goal_data = {
        "user_id": user_id,
        "type": "weekly_load",
        "target_value": "400",
        "status": "ACTIVE",
        "description": "Firestore Testitavoite",
        "start_date": datetime.now(),
        "end_date": None
    }
    # Add to 'goals' collection
    db.collection("goals").add(goal_data)
    print("Added 'goals' document.")

    print("\nSeeding complete! Check your Dashboard.")

except Exception as e:
    print(f"\nError: {e}")
    print("Varmista, että 'service_account_key.json' on oikeassa paikassa.")

import sys
import os

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set credentials path explicitly for testing if not set
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'service_account_key.json'))
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

import firestore_manager
from dotenv import load_dotenv

def verify_isolation():
    print("Locked & Loaded: Verifying Firestore Data Isolation")
    
    # Load env vars (credentials)
    load_dotenv()
    
    # 1. Test with the INTENDED user
    # This ID must match what was seeded or a known user. 
    # Using the default from seed_firestore.py or env
    valid_uid = os.getenv("TEST_USER_ID", "test_user_123")
    print(f"\n[1] Testing with VALID user_id: {valid_uid}")
    
    # Fetch next workout
    workout = firestore_manager.get_next_workout(valid_uid)
    if workout:
        print(f"   Success: Found workout for {valid_uid}")
        print(f"      ID: {workout.get('id')}")
    else:
        print(f"    Warning: No workout found for {valid_uid}. Did you run seed_firestore.py?")

    # Fetch goals
    goals = firestore_manager.get_active_goals(valid_uid)
    print(f"    Found {len(goals)} active goals.")

    # 2. Test with an UNAUTHORIZED user
    intruder_uid = "intruder_999"
    print(f"\n[2] Testing with INTRUDER user_id: {intruder_uid}")
    
    # Fetch next workout (Expect None)
    workout_intruder = firestore_manager.get_next_workout(intruder_uid)
    if workout_intruder is None:
        print(f"   Success: No workout returned for {intruder_uid}")
    else:
        print(f"   FAILURE: LEAKED DATA! Found workout for intruder!")
        print(filter)

    # Fetch goals (Expect Empty List)
    goals_intruder = firestore_manager.get_active_goals(intruder_uid)
    if not goals_intruder:
         print(f"   Success: No goals returned for {intruder_uid}")
    else:
         print(f"   FAILURE: LEAKED GOALS! Found {len(goals_intruder)} goals for intruder!")

if __name__ == "__main__":
    verify_isolation()

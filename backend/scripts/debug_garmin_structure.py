
import sys
import os
import json
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import get_settings

settings = get_settings()
from firestore_manager import get_db, get_garmin_credentials
from garminconnect import Garmin

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Fetching users...")
    db = get_db()
    users_ref = db.collection('users').stream()
    
    users = []
    for doc in users_ref:
        u = doc.to_dict()
        u['uid'] = doc.id
        users.append(u)
    
    if not users:
        logger.error("No users found.")
        return

    # Pick the first user with Garmin credentials
    target_user = None
    target_creds = None
    
    for user in users:
        uid = user['uid']
        creds = get_garmin_credentials(uid)
        if creds:
            target_user = uid
            target_creds = creds
            break
            
    if not target_user:
        logger.error("No users with Garmin credentials found.")
        return
        
    logger.info(f"Using user: {target_user}")
    
    try:
        email = target_creds['username']
        password = target_creds['password']
        
        client = Garmin(email, password)
        client.login()
        logger.info("Garmin login successful.")
        
        # 1. Get List of Workouts
        logger.info("Fetching workouts list...")
        workouts = client.get_workouts() # This usually returns a list of summaries
        
        if not workouts:
            logger.info("No workouts found on Garmin Connect. Cannot verify structure.")
            # Try to create a dummy one to see if we can get a better error? 
            # No, let's just exit.
            return

        logger.info(f"Found {len(workouts)} workouts.")
        
        # 2. Get Full Details of the first workout
        first_workout_id = workouts[0]['workoutId']
        logger.info(f"Fetching details for workout ID: {first_workout_id}")
        
        # api url: /workout-service/workout/{id}
        full_workout = client.connectapi(f"/workout-service/workout/{first_workout_id}")
        
        print("\n--- VALID GARMIN WORKOUT JSON ---")
        print(json.dumps(full_workout, indent=2))
        print("---------------------------------")
        
        # Save to file
        with open("garmin_example_workout.json", "w") as f:
            json.dump(full_workout, f, indent=2)
            logger.info("Saved to garmin_example_workout.json")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

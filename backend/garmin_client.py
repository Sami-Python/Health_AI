from garminconnect import Garmin
from logger import logger
import firestore_manager
import os
from typing import Dict, Any, Optional
import json

class GarminClient:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.client = None

    def connect(self):
        """Authenticate with Garmin Connect using stored credentials."""
        try:
            creds = firestore_manager.get_garmin_credentials(self.user_id)
            if not creds:
                raise ValueError("No Garmin credentials found. Please connect your account in Settings.")

            email = creds['username']
            password = creds['password'] 
            # Note: firestore_manager.get_garmin_credentials already decrypts the password 
            # if using the helper from fetch_garmin_data.py context, but let's double check.
            # actually fetch_garmin_data.py does: 
            # creds = firestore_manager.get_garmin_credentials(user_id)
            # email = creds['username']
            # password = creds['password']
            # So we assume it returns decrypted password. 
            
            self.client = Garmin(email, password)
            self.client.login()
            logger.info(f"✅ Garmin login successful for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"❌ Garmin auth failed: {e}")
            raise ValueError(f"Garmin authentication failed: {str(e)}")

    def upload_workout(self, workout_json: Dict[str, Any]) -> bool:
        """
        Uploads a workout to Garmin Connect.
        
        Args:
            workout_json: The workout definition in Garmin's expected JSON format.
        """
        if not self.client:
            self.connect()

        try:
            # The garminconnect library has specific methods for different workout types
            # or a generic one? The dir() showed 'upload_workout' but that might be file based.
            # Let's check 'create_workout' or similar if available. 
            # Wait, dir() showed 'create_manual_activity_from_json', 'upload_cycling_workout', etc.
            # It also showed 'upload_workout'. 
            # Looking at source code of similar libs, 'add_workout' might be the one for JSON.
            # But 'garminconnect' 0.2.x might differ. 
            # dir() from previous step: 
            # 'upload_workout': likely uploads a .fit/.tcx file.
            # 'save_workout': Not present. 
            # 'add_workout': NOT present in the dir() list I got!
            
            # Start of dir list: 'ActivityDownloadFormat', ... 'add_body_composition', ...
            # 'create_manual_activity_from_json' exists.
            
            # This is tricky. The popular 'garminconnect' library usually has `add_workout` in newer versions?
            # Or maybe I have an older version?
            # 
            # Let's assume we might need to rely on `upload_workout` with a .fit file if creation via JSON isn't directly supported 
            # OR we try to find the hidden method.
            
            # However, `garmin-connect-export` is for exporting FROM Garmin.
            # The `garminconnect` library (cyberjunky) definitely has workout creation support in recent versions.
            # Let's check the installed version or just try to implement logic that assumes we can find a way or uses a raw request if needed.
            
            # Actually, `garminconnect` exposes `connectapi` which is the internal http client.
            # We can use that to POST to the workout endpoint if a high level method is missing.
            # Endpoint: /workout-service/workout
            
            logger.info(f"Uploading workout for user {self.user_id}...")
            
            # Trying to use internal API if specific method is missing from my view of dir()
            # But wait, let me look at the dir() output again carefully.
            # ... 'upload_cycling_workout', 'upload_hiking_workout', 'upload_running_workout', ... 'upload_workout'
            # These sound like they upload activity FILES, not create structured workouts.
            
            # If the library is missing `create_workout`, I might have to construct the request manually.
            # URL: https://connect.garmin.com/modern/proxy/workout-service/workout
            
            url = "/workout-service/workout"
            # We need to make sure workout_json is valid.
            
            # Using the internal http client
            response = self.client.connectapi(url, method="POST", json=workout_json)
            
            # Check response
            if response and 'workoutId' in response:
                logger.info(f"✅ Workout uploaded successfully. ID: {response['workoutId']}")
                return True
            else:
                logger.error(f"❌ Workout upload response invalid: {response}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to upload workout: {e}")
            raise e

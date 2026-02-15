import firebase_admin
from firebase_admin import auth, credentials, firestore
import os
import datetime
import random

# Initialize Firebase
try:
    if os.path.exists('service_account_key.json'):
        cred = credentials.Certificate('service_account_key.json')
        firebase_admin.initialize_app(cred)
    else:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'personal-ai-coach-92c39')
        firebase_admin.initialize_app(options={'projectId': project_id})
    
    db = firestore.client()
    print("Firebase initialized.")

except Exception as e:
    print(f"Initialization error: {e}")
    # If already initialized, that's fine (e.g. running in same process)

def generate_data():
    email = "sami@personalaicoach.ai"
    try:
        user = auth.get_user_by_email(email)
        user_id = user.uid
        print(f"Found user: {email} (UID: {user_id})")
    except auth.UserNotFoundError:
        print(f"User {email} not found. Please run create_user.py first.")
        return

    # 1. Generate Metrics (Last 7 days + Today)
    print("Generating metrics...")
    today = datetime.date.today()
    
    for i in range(8):
        date_obj = today - datetime.timedelta(days=7-i)
        date_str = date_obj.isoformat()
        
        # Random realistic values
        sleep_min = random.randint(360, 540) # 6h - 9h
        readiness = random.randint(40, 95)
        ctl = 40 + (i * 0.5)
        atl = 35 + (i * 2) if i % 2 == 0 else 20
        tsb = ctl - atl
        
        metric_data = {
            "user_id": user_id,
            "date": date_str,
            "totalSleep_minutes": sleep_min,
            "bodyBatteryHighestValue": readiness,
            "CTL": ctl,
            "ATL": atl,
            "TSB": tsb,
            "workout_calories": random.randint(500, 800) if i % 2 == 0 else 0,
            "totalDistanceMeters": 5500.0 if i % 2 == 0 else 0.0,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        
        # Save to garmin_metrics/{uid}/daily_metrics/{date}
        db.collection('garmin_metrics').document(user_id)\
          .collection('daily_metrics').document(date_str)\
          .set(metric_data, merge=True)

    print(f"Inserted metrics for {today} and previous 7 days.")

    # 2. Generate Active Goal
    print("Generating goal...")
    goals_ref = db.collection('goals')
    # Check if goal exists to verify overwrite
    goals = goals_ref.where('user_id', '==', user_id).stream()
    has_goal = False
    for g in goals:
        has_goal = True
        break
        
    if not has_goal:
        goal_data = {
            "user_id": user_id,
            "activity_type": "Running",
            "target_value": 40.0,
            "target_unit": "km",
            "period_type": "WEEKLY",
            "status": "ACTIVE",
            "current_value": 25.5,
            "progress_percentage": 63,
            "days_left": 2,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        db.collection('goals').add(goal_data)
        print("Inserted active running goal.")
    else:
        print("Goal already exists, skipping.")

    # 3. Generate Workouts (Past)
    print("Generating past workouts...")
    workouts_ref = db.collection('workouts')
    
    # Add a completed run yesterday
    yesterday_str = (today - datetime.timedelta(days=1)).isoformat()
    workout_data = {
        "user_id": user_id,
        "activity": "Running",
        "date": yesterday_str,
        "duration_min": 45,
        "rpe": 6,
        "load_estimate": 45 * 6,
        "status": "DONE",
        "description": "Easy recovery run",
        "created_at": firestore.SERVER_TIMESTAMP
    }
    db.collection('workouts').add(workout_data)
    print("Inserted past workout.")

    print("Done! Refresh the app (Pull down or press Restart).")

if __name__ == "__main__":
    generate_data()

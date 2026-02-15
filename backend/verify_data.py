import firebase_admin
from firebase_admin import auth, credentials, firestore
import os
import datetime

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

def verify():
    email = "sami@personalaicoach.ai"
    try:
        user = auth.get_user_by_email(email)
        user_id = user.uid
        print(f"Found user: {email} (UID: {user_id})")
    except:
        print("User not found")
        return

    # 1. Calc Date Range for Weekly Goal
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=today.weekday())
    end_date = start_date + datetime.timedelta(days=6)
    
    print(f"Weekly Goal Range: {start_date} to {end_date}")

    # 2. Fetch Metrics in Range
    print("\n--- Metrics in Range ---")
    docs = db.collection('garmin_metrics').document(user_id)\
             .collection('daily_metrics')\
             .where('date', '>=', start_date.isoformat())\
             .where('date', '<=', end_date.isoformat())\
             .order_by('date').stream()
    
    total_dist = 0
    count = 0
    for doc in docs:
        d = doc.to_dict()
        dist = d.get('totalDistanceMeters', 'MISSING')
        print(f"Date: {d.get('date')} | Dist: {dist}")
        if isinstance(dist, (int, float)):
            total_dist += dist
        count += 1
    
    print(f"Total Docs: {count}")
    print(f"Total Distance (m): {total_dist}")
    print(f"Total Distance (km): {total_dist / 1000.0}")

    # 3. Check Goals
    print("\n--- Goals ---")
    goals = db.collection('goals').where('user_id', '==', user_id).stream()
    for g in goals:
        gd = g.to_dict()
        print(f"Goal: {gd.get('activity_type')} {gd.get('target_value')}{gd.get('target_unit')}")
        print(f"Period: {gd.get('period_type')}")

if __name__ == "__main__":
    verify()

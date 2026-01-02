import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

# Initialize Firestore
# It expects GOOGLE_APPLICATION_CREDENTIALS env var or explicit path
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account_key.json")

if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        print(f"Warning: Firestore credential file not found at {cred_path}. Firestore will fail.")

db = firestore.client()

def get_next_workout(user_id: str):
    """Fetches next pending workout from 'workouts' collection for specific user."""
    try:
        # Filter by user_id
        # Query: status == 'PENDING', user_id == uid, order by date, limit 1
        docs = db.collection('workouts').where('user_id', '==', user_id).where('status', '==', 'PENDING').limit(1).stream()
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None
    except Exception as e:
        print(f"Firestore Error: {e}")
        return None

def get_active_goals(user_id: str):
    """Fetches active goals for specific user."""
    try:
        docs = db.collection('goals').where('user_id', '==', user_id).where('status', '==', 'ACTIVE').stream()
        return [d.to_dict() for d in docs]
    except Exception as e:
         print(f"Firestore Error: {e}")
         return []

def get_weekly_load_status(user_id: str):
    """Aggregates weekly stats (Mock logic for now as Firestore aggregations are different)."""
    # This is complex in NoSQL. For now returning empty skeleton.
    # This is complex in NoSQL. For now returning empty skeleton.
    return 0, 0, {}

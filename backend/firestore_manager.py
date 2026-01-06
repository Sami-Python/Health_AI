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
        goals = []
        for d in docs:
            g = d.to_dict()
            g['id'] = d.id
            goals.append(g)
        return goals
    except Exception as e:
         print(f"Firestore Error: {e}")
         return []

def get_weekly_load_status(user_id: str):
    """Aggregates weekly stats (Mock logic for now as Firestore aggregations are different)."""
    # This is complex in NoSQL. For now returning empty skeleton.
    # This is complex in NoSQL. For now returning empty skeleton.
    return 0, 0, {}

def add_goal(user_id: str, goal_data: dict):
    """Adds a new goal for the specific user."""
    try:
        # Add user_id to goal_data ensuring ownership
        goal_data['user_id'] = user_id
        if 'status' not in goal_data:
            goal_data['status'] = 'ACTIVE'
        
        # Add timestamp
        goal_data['created_at'] = firestore.SERVER_TIMESTAMP

        db.collection('goals').add(goal_data)
        return True
    except Exception as e:
        print(f"Firestore Error: {e}")
        return False

def delete_goal(user_id: str, goal_id: str):
    """Deletes a goal."""
    try:
        # Verify ownership
        doc_ref = db.collection('goals').document(goal_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        
        if doc.to_dict().get('user_id') != user_id:
            return False
            
        doc_ref.delete()
        return True
    except Exception as e:
        print(f"Firestore Error: {e}")
        return False

def update_goal(user_id: str, goal_id: str, updates: dict):
    """Updates a goal."""
    try:
        doc_ref = db.collection('goals').document(goal_id)
        doc = doc_ref.get()
        if not doc.exists or doc.to_dict().get('user_id') != user_id:
            return False
            
        doc_ref.update(updates)
        return True
    except Exception as e:
        print(f"Firestore Error: {e}")
        return False

def save_generated_plan(user_id: str, plan_data: dict, advice_text: str, predicted_charge: int):
    """Saves AI generated plan context and advice."""
    try:
        doc_data = {
            'user_id': user_id,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'advice': advice_text,
            'charge': predicted_charge,
            'context': plan_data, # JSON blob of context
            'type': 'daily_plan'
        }
        db.collection('plans').add(doc_data)
        return True
    except Exception as e:
        print(f"Firestore Error: {e}")
        return False

def get_recent_plans(user_id: str, limit: int = 5):
    """Fetches recent AI coaching plans."""
    try:
        # Order by timestamp descending
        docs = db.collection('plans')\
                 .where('user_id', '==', user_id)\
                 .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                 .limit(limit)\
                 .stream()
        
        plans = []
        for d in docs:
            data = d.to_dict()
            # Convert timestamp to string
            if 'timestamp' in data and data['timestamp']:
                 data['timestamp'] = data['timestamp'].isoformat()
            data['id'] = d.id
            plans.append(data)
        return plans
    except Exception as e:
        print(f"Firestore history error: {e}")
        return []

def save_workout(user_id: str, workout: dict):
    """Saves a completed or manual workout."""
    try:
        workout['user_id'] = user_id
        workout['created_at'] = firestore.SERVER_TIMESTAMP
        db.collection('workouts').add(workout)
        return True
    except Exception as e:
        print(f"Firestore Save Error: {e}")
        return False

def get_upcoming_workouts(user_id: str):
    """Fetches upcoming workouts (today onwards)."""
    try:
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Simple query: where date >= today
        # Note: In a real app, 'date' string comparison works for ISO dates 'YYYY-MM-DD'
        docs = db.collection('workouts')\
                 .where('user_id', '==', user_id)\
                 .where('date', '>=', today_str)\
                 .stream()
                 
        workouts = []
        for d in docs:
            w = d.to_dict()
            w['id'] = d.id
            if 'date' in w:
                w['load'] = w.get('load_estimate', 0) # Map estimate to load for simple Viz
                workouts.append(w)
        return workouts
    except Exception as e:
        print(f"Firestore Error: {e}")
        return []

def delete_pending_workouts(user_id: str, start_date: str, end_date: str):
    """Deletes pending workouts in date range (inclusive)."""
    try:
        # Simplified query: user_id + date range only.
        # Filter 'status' == 'PENDING' in memory to avoid needing a specific composite index.
        docs = db.collection('workouts')\
                 .where('user_id', '==', user_id)\
                 .where('date', '>=', start_date)\
                 .where('date', '<=', end_date)\
                 .stream()
        
        batch = db.batch()
        count = 0
        deleted_count = 0
        
        for d in docs:
            data = d.to_dict()
            if data.get('status') == 'PENDING':
                batch.delete(d.reference)
                deleted_count += 1
                count += 1
            
            # Commit in batches of 400 if needed (Firestore limit is 500)
            if count >= 400:
                batch.commit()
                batch = db.batch()
                count = 0
                
        if count > 0:
            batch.commit()
            
        if deleted_count > 0:
            print(f"Deleted {deleted_count} pending workouts.")
            
        return True
    except Exception as e:
        print(f"Firestore Delete Error: {e}")
        return False

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
from datetime import datetime
from google.cloud.firestore import FieldFilter

# Lazy Initialization Pattern
# Firestore connection is deferred until first API request
# This allows FastAPI server to start immediately in Cloud Run
import secret_loader

# Global state for lazy initialization
_db = None
_initialized = False
_init_lock = False  # Simple lock to prevent concurrent initialization

def _ensure_initialized():
    """
    Lazy initialization of Firestore client.
    Called automatically by get_db() on first use.
    """
    global _db, _initialized, _init_lock
    
    if _initialized:
        return
    
    # Simple lock to prevent concurrent initialization
    if _init_lock:
        import time
        while _init_lock and not _initialized:
            time.sleep(0.1)
        return
    
    _init_lock = True
    
    try:
        cred_source = secret_loader.get_service_account_dict()
        
        if not firebase_admin._apps:
            if cred_source:
                cred = credentials.Certificate(cred_source)
                firebase_admin.initialize_app(cred)
            else:
                # Fallback: Application Default Credentials (Cloud Run)
                print("Warning: No specific credential found. Trying Application Default Credentials...")
                
                # FIX: Explicitly specify Project ID to avoid mismatch between Cloud Run project and Firebase Auth project
                from config import get_settings
                settings = get_settings()
                print(f"Initializing Firebase with Target Project ID: {settings.FIREBASE_PROJECT_ID}")
                
                firebase_admin.initialize_app(options={
                    'projectId': settings.FIREBASE_PROJECT_ID
                })
        
        _db = firestore.client()
        _initialized = True
        print("[SUCCESS] Firestore initialized successfully")
        
    except Exception as e:
        print(f"[ERROR] Firestore initialization failed: {e}")
        raise
    finally:
        _init_lock = False

def get_db():
    """
    Get Firestore client, initializing if needed.
    This is the main entry point for all Firestore operations.
    """
    _ensure_initialized()
    return _db

# Legacy compatibility: db attribute for backward compatibility
# This will initialize on first access
class _LazyDB:
    def __getattr__(self, name):
        return getattr(get_db(), name)

db = _LazyDB()

def get_next_workout(user_id: str):
    """Fetches next pending workout from 'workouts' collection for specific user."""
    try:
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Query: status == 'PENDING', date >= today, order by date, limit 1
        docs = db.collection('users').document(user_id).collection('workouts')\
                 .where(filter=FieldFilter('status', '==', 'PENDING'))\
                 .where(filter=FieldFilter('date', '>=', today_str))\
                 .order_by('date')\
                 .limit(1)\
                 .stream()
                 
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            # Frontend expects 'content' field with 'activity' inside, or direct fields.
            # DuckDB stored complex JSON in 'content'. Firestore stores fields directly often.
            # Let's verify how we save. We save: date, activity, duration_min, rpe, description...
            # The frontend 'nextWorkout' card uses: nextWorkout?.content?.activity || "Rest Day"
            # So we need to structure it to match what frontend expects OR update frontend.
            # Updating frontend is expensive, let's map it here.
            
            mapped_content = {
                "activity": data.get('activity', 'Workout'),
                "description": data.get('description', '')
            }
            
            return {
                "id": doc.id,
                "content": mapped_content,
                "date": data.get('date')
            }
        return None
    except Exception as e:
        print(f"Firestore Error (Next Workout): {e}")
        return None

def get_active_goals(user_id: str):
    """Fetches active goals for specific user."""
    try:
        docs = db.collection('users').document(user_id).collection('goals').where(filter=FieldFilter('status', '==', 'ACTIVE')).stream()
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
    """Aggregates weekly stats from Firestore."""
    try:
        from datetime import datetime, timedelta
        today = datetime.now().date()
        start_date = today - timedelta(days=6) # Last 7 days
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = today.strftime('%Y-%m-%d')
        
        # Fetch all workouts in range
        docs = db.collection('users').document(user_id).collection('workouts')\
                 .where(filter=FieldFilter('date', '>=', start_str))\
                 .where(filter=FieldFilter('date', '<=', end_str))\
                 .stream()
                 
        current_load = 0
        planned_load = 0
        duration_min = 0 # New field
        
        # Calculate daily breakdown for the graph
        breakdown = {}
        for i in range(7):
            day = start_date + timedelta(days=i)
            breakdown[day.strftime('%Y-%m-%d')] = {"current": 0, "planned": 0}
        
        for doc in docs:
            data = doc.to_dict()
            load = data.get('load_estimate', 0)
            duration = data.get('duration_min', 0) # Track duration
            workout_date = data.get('date')
            
            # If manual log, calculate load if missing
            if load == 0 and 'duration_min' in data and 'rpe' in data:
                load = data['duration_min'] * data['rpe']
            
            # Garmin fallback for Weekly Load card if activityTrainingLoad is missing
            if load == 0 and data.get('source') == 'GARMIN':
                # Assume moderate intensity (5) for Garmin sessions if load is 0
                load = duration * 5
                
            planned_load += load
            duration_min += duration # Aggregate Total Duration
            
            if workout_date in breakdown:
                breakdown[workout_date]["planned"] += load
                if data.get('status') == 'DONE':
                    breakdown[workout_date]["current"] += load
            
            if data.get('status') == 'DONE':
                current_load += load
                
        return current_load, planned_load, breakdown, duration_min
    except Exception as e:
        print(f"Firestore Error (Weekly Load): {e}")
        return 0, 0, {}

def get_latest_readiness(user_id: str):
    """Fetches latest readiness (projected charge) from plans and last sync time from profile."""
    try:
        result = {
            "readiness": "--",
            "date": "",
            "last_sync_time": None
        }
        
        # 1. Get latest plan charge
        docs = db.collection('users').document(user_id).collection('plans')\
                 .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                 .limit(1)\
                 .stream()
                 
        for doc in docs:
            data = doc.to_dict()
            result["readiness"] = data.get('charge', 80)
            result["date"] = data.get('timestamp', datetime.now()).strftime('%Y-%m-%d') if isinstance(data.get('timestamp'), datetime) else str(data.get('timestamp'))
            
        # 2. Get last sync time from user profile
        user_doc = db.collection('users').document(user_id).collection('profile').document('metrics').get()
        if user_doc.exists:
            result["last_sync_time"] = user_doc.to_dict().get('last_sync_time')
            
        # Fallback to general user document if not in metrics
        if not result["last_sync_time"]:
            user_main = db.collection('users').document(user_id).get()
            if user_main.exists:
                result["last_sync_time"] = user_main.to_dict().get('last_sync_time')
                
        # 3. CRITICAL FALLBACK: If readiness is still "--", use current body battery from daily_metrics
        if result["readiness"] == "--":
            try:
                # Import here to avoid circular dependencies
                import firestore_garmin_metrics
                latest_metric = firestore_garmin_metrics.get_latest_metric(user_id)
                if latest_metric:
                    # Use Highest Value or Charge as proxy for readiness if prediction is missing
                    result["readiness"] = latest_metric.get('bodyBatteryHighestValue', latest_metric.get('bodyBatteryChargedValue', "--"))
                    if result["date"] == "":
                        result["date"] = latest_metric.get('date', "")
            except Exception as fe:
                print(f"Readiness Fallback Error: {fe}")

        # Handle datetime serialization if it's a Firestore Datetime
        if isinstance(result["last_sync_time"], datetime):
            result["last_sync_time"] = result["last_sync_time"].isoformat()
            
        return result if result["readiness"] != "--" or result["last_sync_time"] else None
    except Exception as e:
        print(f"Firestore Error (Readiness): {e}")
        return None

def add_goal(user_id: str, goal_data: dict):
    """Adds a new goal for the specific user."""
    try:
        # Add user_id to goal_data ensuring ownership
        goal_data['user_id'] = user_id
        if 'status' not in goal_data:
            goal_data['status'] = 'ACTIVE'
        
        # Add timestamp
        goal_data['created_at'] = firestore.SERVER_TIMESTAMP

        db.collection('users').document(user_id).collection('goals').add(goal_data)
        return True
    except Exception as e:
        print(f"Firestore Error: {e}")
        return False

def delete_goal(user_id: str, goal_id: str):
    """Deletes a goal."""
    try:
        # Verify ownership (implicit in nested structure, but checking existance)
        doc_ref = db.collection('users').document(user_id).collection('goals').document(goal_id)
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
        doc_ref = db.collection('users').document(user_id).collection('goals').document(goal_id)
        doc = doc_ref.get()
        if not doc.exists:
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
        db.collection('users').document(user_id).collection('plans').add(doc_data)
        return True
    except Exception as e:
        print(f"Firestore Error: {e}")
        return False

def get_recent_plans(user_id: str, limit: int = 5):
    """Fetches recent AI coaching plans."""
    try:
        # Order by timestamp descending
        docs = db.collection('users').document(user_id).collection('plans')\
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

def _match_and_score_pending_workout(user_id: str, workout_data: dict):
    workout_date = workout_data.get('date')
    if not workout_date:
        return
        
    docs = db.collection('users').document(user_id).collection('workouts')\
             .where(filter=FieldFilter('date', '==', workout_date))\
             .where(filter=FieldFilter('status', '==', 'PENDING'))\
             .stream()
             
    planned_workout = None
    planned_doc_ref = None
    for d in docs:
        planned_workout = d.to_dict()
        planned_doc_ref = d.reference
        break
        
    if planned_workout:
        p_dur = planned_workout.get('duration_min', 0)
        p_load = planned_workout.get('load_estimate', 0)
        a_dur = workout_data.get('duration_min', 0)
        a_load = workout_data.get('load_estimate', 0)
        
        dur_score = min(100, (a_dur / p_dur * 100)) if p_dur > 0 else (100 if a_dur > 0 else 0)
        load_score = min(100, (a_load / p_load * 100)) if p_load > 0 else (100 if a_load > 0 else 0)
        
        execution_score = int((dur_score * 0.5) + (load_score * 0.5))
        
        workout_data['execution_score'] = execution_score
        workout_data['planned_duration'] = p_dur
        workout_data['planned_load'] = p_load
        
        # Keep planned structure if available and actual is missing
        if 'structure' not in workout_data or not workout_data['structure']:
            workout_data['structure'] = planned_workout.get('structure', '')
            
        planned_doc_ref.delete()

def get_average_execution_score(user_id: str, days: int = 7):
    """Calculates average execution score from the past N days."""
    try:
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        docs = db.collection('users').document(user_id).collection('workouts')\
                 .where(filter=FieldFilter('status', '==', 'DONE'))\
                 .where(filter=FieldFilter('date', '>=', start_date))\
                 .stream()
                 
        scores = []
        for d in docs:
            data = d.to_dict()
            if 'execution_score' in data:
                scores.append(data['execution_score'])
                
        if scores:
            return sum(scores) / len(scores)
        return None
    except Exception as e:
        print(f"Firestore Error (Execution Score): {e}")
        return None

def get_gamification_summary(user_id: str):
    """Calculates consistency score, streak, and badges from recent completed workouts."""
    try:
        from datetime import datetime, timedelta
        
        # Fetch all DONE workouts from the last 30 days (for streak and 14-day avg)
        start_date_30 = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        docs = db.collection('users').document(user_id).collection('workouts')\
                 .where(filter=FieldFilter('status', '==', 'DONE'))\
                 .where(filter=FieldFilter('date', '>=', start_date_30))\
                 .stream()
                 
        workouts = []
        for d in docs:
            data = d.to_dict()
            if 'execution_score' in data and 'date' in data:
                workouts.append(data)
                
        # Sort by date descending (newest first)
        workouts.sort(key=lambda x: x['date'], reverse=True)
        
        # 1. Calculate 14-day consistency score
        start_date_14 = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        recent_14_scores = [w['execution_score'] for w in workouts if w['date'] >= start_date_14]
        consistency_score = int(sum(recent_14_scores) / len(recent_14_scores)) if recent_14_scores else 0
        
        # 2. Calculate Streak (consecutive logged workouts with execution_score >= 80)
        streak = 0
        for w in workouts:
            if w['execution_score'] >= 80:
                streak += 1
            else:
                break
                
        # 3. Evaluate Badges
        badges = []
        if consistency_score >= 60:
            badges.append({"id": "bronze", "name": "Solid Base", "icon": "🥉", "level": "bronze"})
        if consistency_score >= 80:
            badges.append({"id": "silver", "name": "Dedicated", "icon": "🥈", "level": "silver"})
        if consistency_score >= 95:
            badges.append({"id": "gold", "name": "AI's Favorite", "icon": "🥇", "level": "gold"})
        if streak >= 7:
            badges.append({"id": "fire", "name": "7-Day Streak", "icon": "🔥", "level": "special"})
            
        return {
            "consistency_score": consistency_score,
            "streak": streak,
            "badges": badges
        }
    except Exception as e:
        print(f"Firestore Error (Gamification): {e}")
        return {
            "consistency_score": 0,
            "streak": 0,
            "badges": []
        }

def save_workout(user_id: str, workout_data: dict):
    """Saves a workout to the 'workouts' collection."""
    try:
        workout_data['user_id'] = user_id
        workout_data['created_at'] = firestore.SERVER_TIMESTAMP
        
        if workout_data.get('status') == 'DONE':
            _match_and_score_pending_workout(user_id, workout_data)
            
        db.collection('users').document(user_id).collection('workouts').add(workout_data)
        return True
    except Exception as e:
        print(f"Firestore Error: {e}")
        return False

def save_garmin_workout(user_id: str, workout_data: dict, activity_id: str):
    """Upserts a Garmin workout using its original activityId."""
    try:
        workout_data['user_id'] = user_id
        workout_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        if workout_data.get('status') == 'DONE':
            _match_and_score_pending_workout(user_id, workout_data)
            
        # Use .set with merge=True to update or create
        db.collection('users').document(user_id).collection('workouts').document(str(activity_id)).set(workout_data, merge=True)
        return True
    except Exception as e:
        print(f"Firestore Error (Garmin Sync): {e}")
        return False

def get_daily_insight(user_id: str, date_str: str):
    """Checks cache for existing daily insight."""
    try:
        doc = db.collection('users').document(user_id).collection('daily_insights').document(date_str).get()
        if doc.exists:
            return doc.to_dict().get('insight')
        return None
    except Exception as e:
        print(f"Firestore Cache Read Error: {e}")
        return None

def save_daily_insight(user_id: str, date_str: str, insight: str):
    """Saves daily insight to cache."""
    try:
        db.collection('users').document(user_id).collection('daily_insights').document(date_str).set({
            "insight": insight,
            "created_at": firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"Firestore Cache Save Error: {e}")

def get_upcoming_workouts(user_id: str):
    """
    Fetches upcoming workouts (today onwards) from user's sub-collection.
    Optimized to avoid composite index requirements (status + date).
    """
    try:
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Simple query: just by date
        docs = db.collection('users').document(user_id)\
                 .collection('workouts')\
                 .where(filter=FieldFilter('date', '>=', today_str))\
                 .stream()
                 
        workouts = []
        for d in docs:
            w = d.to_dict()
            w['id'] = d.id
            
            # Filter PENDING in memory to avoid needing composite index (status, date)
            if w.get('status') == 'PENDING' and 'date' in w:
                w['load'] = w.get('load_estimate', 0)
                workouts.append(w)
        
        # Sort by date
        workouts.sort(key=lambda x: x.get('date', ''))
        return workouts
    except Exception as e:
        print(f"Firestore Error (Upcoming Memory Filter): {e}")
        return []

def get_workouts_in_range(user_id: str, start_date: str, end_date: str):
    """Fetches workouts within a date range from user's sub-collection."""
    try:
        docs = db.collection('users').document(user_id)\
                 .collection('workouts')\
                 .where(filter=FieldFilter('date', '>=', start_date))\
                 .where(filter=FieldFilter('date', '<=', end_date))\
                 .stream()
        
        workouts = []
        for d in docs:
            w = d.to_dict()
            w['id'] = d.id
            workouts.append(w)
        return workouts
    except Exception as e:
        print(f"Firestore Error (Range): {e}")
        return []

def delete_pending_workouts(user_id: str, start_date: str, end_date: str):
    """
    Deletes pending workouts in date range (inclusive).
    Optimized to avoid composite index requirements by filtering PENDING in memory if needed,
    but here we use the specific collection path.
    """
    try:
        # Fetch pending workouts for user in standard sub-collection
        query = db.collection('users').document(user_id).collection('workouts')\
                  .where(filter=FieldFilter('status', '==', 'PENDING'))
        
        # We fetch and filter dates in memory to avoid "Missing Index" errors on range + inequality
        docs = query.stream()
        
        batch = db.batch()
        deleted_count = 0
        total_processed = 0
        
        for d in docs:
            data = d.to_dict()
            workout_date = data.get('date', '')
            
            # Date range check
            if start_date <= workout_date <= end_date:
                batch.delete(d.reference)
                deleted_count += 1
                total_processed += 1
            
                if total_processed >= 400:
                    batch.commit()
                    batch = db.batch()
                    total_processed = 0
                
        if total_processed > 0:
            batch.commit()
            
        if deleted_count > 0:
            print(f"[CLEANUP] Deleted {deleted_count} stale pending workouts for {user_id}")
            
        return True
    except Exception as e:
        print(f"Firestore Cleanup Error: {e}")
        return False


def get_user_profile(user_id: str):
    """Fetches user profile data."""
    try:
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return {} # Return empty dict if no profile yet
    except Exception as e:
        print(f"Firestore Profile Error: {e}")
        return {}

def update_user_profile(user_id: str, data: dict):
    """Updates or creates user profile data."""
    try:
        doc_ref = db.collection('users').document(user_id)
        # set(..., merge=True) creates if not exists and updates fields
        doc_ref.set(data, merge=True)
        return True
    except Exception as e:
        return False

def save_fcm_token(user_id: str, token: str):
    """Saves the user's FCM token for push notifications."""
    try:
        db.collection('users').document(user_id).set({'fcm_token': token}, merge=True)
        return True
    except Exception as e:
        print(f"Error saving FCM token: {e}")
        return False

def get_fcm_token(user_id: str):
    """Retrieves the user's FCM token."""
    try:
        doc = db.collection('users').document(user_id).get()
        if doc.exists:
            return doc.to_dict().get('fcm_token')
        return None
    except Exception as e:
        print(f"Error getting FCM token: {e}")
        return None

def get_last_missed_workout(user_id: str):
    """
    Finds the SINGLE most recent PENDING workout before today.
    Returns the workout dict or None.
    """
    try:
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Query: PENDING workouts where date < today, ordered by date descending
        docs = db.collection('users').document(user_id).collection('workouts')\
                 .where(filter=FieldFilter('status', '==', 'PENDING'))\
                 .where(filter=FieldFilter('date', '<', today_str))\
                 .order_by('date', direction='DESCENDING')\
                 .limit(1)\
                 .stream()
        
        for d in docs:
            w = d.to_dict()
            w['id'] = d.id
            return w
            
        return None
    except Exception as e:
        print(f"Error fetching missed workout: {e}")
        return None


def update_workout_date(user_id: str, workout_id: str, new_date: str):
    """Updates the date of a specific workout (Drag & Drop)."""
    try:
        doc_ref = db.collection('workouts').document(workout_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return False
            
        if doc.to_dict().get('user_id') != user_id:
            return False
            
        doc_ref.update({'date': new_date})
        return True
    except Exception as e:
        print(f"Update Date Error: {e}")
        return False

def check_daily_generation_limit(user_id: str, max_limit: int = 5):
    """Checks if user has exceeded daily generation limit."""
    try:
        from datetime import datetime, time
        # Get start and end of today
        now = datetime.now()
        start_of_day = datetime.combine(now.date(), time.min)
        
        # Count plans generated today
        docs = db.collection('plans')\
                 .where(filter=FieldFilter('user_id', '==', user_id))\
                 .where(filter=FieldFilter('timestamp', '>=', start_of_day))\
                 .stream()
                 
        count = sum(1 for _ in docs)
        return count  < max_limit
    except Exception as e:
        print(f"Limit Check Error: {e}")
        # Fail open or closed? Let's fail open but log error
        return True

def check_daily_generation_limit(user_id: str, max_limit: int = 5):
    """Checks if user has exceeded daily generation limit."""
    try:
        from datetime import datetime, time
        # Get start and end of today
        now = datetime.now()
        start_of_day = datetime.combine(now.date(), time.min)
        
        # Count plans generated today
        docs = db.collection('plans')\
                 .where(filter=FieldFilter('user_id', '==', user_id))\
                 .where(filter=FieldFilter('timestamp', '>=', start_of_day))\
                 .stream()
                 
        count = sum(1 for _ in docs)
        return count < max_limit
    except Exception as e:
        print(f"Limit Check Error: {e}")
        # Fail open or closed? Let's fail open but log error
        return True

def delete_all_user_data(user_id: str):
    """Deletes ALL user data from Firestore (GDPR Compliance)."""
    try:
        # Collections to delete: goals, workouts, plans, users (profile + subcollections)
        collections = ['goals', 'workouts', 'plans']
        
        batch = db.batch()
        count = 0
        
        for collection_name in collections:
            docs = db.collection(collection_name)\
                     .where(filter=FieldFilter('user_id', '==', user_id))\
                     .stream()
            
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
                
                # Firestore batch limit is 500 operations
                if count >= 400:
                    batch.commit()
                    batch = db.batch()
                    count = 0
        
        # Delete user profile and subcollections
        user_ref = db.collection('users').document(user_id)
        
        # Delete daily_insights subcollection
        insights = user_ref.collection('daily_insights').stream()
        for insight in insights:
            batch.delete(insight.reference)
            count += 1
            if count >= 400:
                batch.commit()
                batch = db.batch()
                count = 0
        
        # Delete garmin_credentials subcollection (GDPR - encrypted passwords)
        delete_garmin_credentials(user_id)
        
        # Delete user profile document
        batch.delete(user_ref)
        count += 1
        
        # Final commit
        if count > 0:
            batch.commit()
        
        # Delete Garmin metrics (separate collection structure)
        # Import here to avoid circular dependency at module level
        import firestore_garmin_metrics
        firestore_garmin_metrics.delete_user_metrics(user_id)
        
        # Delete user feedback submissions
        delete_user_feedback(user_id)
        
        print(f"[SUCCESS] Deleted ALL data for user {user_id} (GDPR compliant)")
        return True
        
    except Exception as e:
        print(f"[ERROR] User Data Deletion Error: {e}")
        return False
"""
GDPR Compliance Helper Functions
Adds data export and feedback functionality to firestore_manager
"""
from google.cloud.firestore import FieldFilter

# Import the shared db client
import firestore_manager

db = firestore_manager.db

def get_all_goals(user_id: str):
    """Fetches ALL goals for a user (active and archived) for data export."""
    try:
        docs = db.collection('goals').where(filter=FieldFilter('user_id', '==', user_id)).stream()
        goals = []
        for d in docs:
            g = d.to_dict()
            g['id'] = d.id
            # Convert Firestore timestamps to ISO strings
            if 'created_at' in g and g['created_at']:
                try:
                    g['created_at'] = g['created_at'].isoformat()
                except:
                    pass
            goals.append(g)
        return goals
    except Exception as e:
        print(f"Firestore Error (get_all_goals): {e}")
        return []

def get_all_workouts(user_id: str, limit: int = 1000):
    """Fetches all workouts for a user (capped at limit for performance)."""
    try:
        docs = db.collection('users').document(user_id).collection('workouts')\
                 .order_by('date', direction='DESCENDING')\
                 .limit(limit)\
                 .stream()
        
        workouts = []
        for d in docs:
            w = d.to_dict()
            w['id'] = d.id
            # Convert timestamps
            if 'created_at' in w and w['created_at']:
                try:
                    w['created_at'] = w['created_at'].isoformat()
                except:
                    pass
            if 'updated_at' in w and w['updated_at']:
                try:
                    w['updated_at'] = w['updated_at'].isoformat()
                except:
                    pass
            workouts.append(w)
        return workouts
    except Exception as e:
        print(f"Firestore Error (get_all_workouts): {e}")
        return []

def save_feedback(user_id: str, feedback_data: dict):
    """Saves user feedback to Firestore."""
    try:
        from firebase_admin import firestore as fb_firestore
        feedback_data['user_id'] = user_id
        feedback_data['timestamp'] = fb_firestore.SERVER_TIMESTAMP
        feedback_data['status'] = 'NEW'
        db.collection('feedback').add(feedback_data)
        return True
    except Exception as e:
        print(f"Firestore Error (save_feedback): {e}")
        return False

def delete_user_feedback(user_id: str) -> bool:
    """
    Deletes all feedback submitted by a user (GDPR compliance).
    
    Args:
        user_id: Firebase UID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        docs = db.collection('feedback')\
                 .where(filter=FieldFilter('user_id', '==', user_id))\
                 .stream()
        
        batch = db.batch()
        count = 0
        
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            
            if count >= 400:
                batch.commit()
                batch = db.batch()
                count = 0
        
        if count > 0:
            batch.commit()
        
        if count > 0:
            print(f"[DELETED] Deleted {count} feedback documents for user {user_id}")
        
        return True
        
    except Exception as e:
        print(f"Firestore Error (delete_user_feedback): {e}")
        return False

def get_all_feedback(limit: int = 100):
    """Fetches all feedback for admin review (NO user_id filter)."""
    try:
        docs = db.collection('feedback')\
                 .order_by('timestamp', direction='DESCENDING')\
                 .limit(limit)\
                 .stream()
        
        feedback_list = []
        for d in docs:
            f = d.to_dict()
            f['id'] = d.id
            # Convert timestamp
            if 'timestamp' in f and f['timestamp']:
                try:
                    f['timestamp'] = f['timestamp'].isoformat()
                except:
                    pass
            feedback_list.append(f)
        return feedback_list
    except Exception as e:
        print(f"Firestore Error (get_all_feedback): {e}")
        return []

# ========================================
# Garmin Credentials (Encrypted Storage)
# ========================================

def save_garmin_credentials(user_id: str, username: str, password: str) -> bool:
    """
    Encrypts and saves Garmin credentials to Firestore.
    
    Args:
        user_id: Firebase UID
        username: Garmin email/username (stored in plaintext)
        password: Garmin password (encrypted before storage)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from encryption_helper import encrypt_password
        
        # Encrypt password
        encrypted_password = encrypt_password(password)
        
        # Store in users/{uid}/garmin_credentials subcollection
        doc_ref = db.collection('users').document(user_id).collection('garmin_credentials').document('default')
        
        doc_ref.set({
            'username': username,  # Plaintext (email address is not sensitive in Firestore)
            'password_encrypted': encrypted_password,
            'created_at': firestore.SERVER_TIMESTAMP,
            'last_updated': firestore.SERVER_TIMESTAMP
        })
        
        print(f"[SUCCESS] Garmin credentials saved for user: {user_id}")
        return True
        
    except Exception as e:
        print(f"Firestore Error (save_garmin_credentials): {e}")
        return False


def get_garmin_credentials(user_id: str) -> dict | None:
    """
    Retrieves and decrypts Garmin credentials.
    
    Args:
        user_id: Firebase UID
        
    Returns:
        {"username": "...", "password": "..."} or None if not found
    """
    try:
        from encryption_helper import decrypt_password
        
        doc_ref = db.collection('users').document(user_id).collection('garmin_credentials').document('default')
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        
        # Decrypt password
        decrypted_password = decrypt_password(data['password_encrypted'])
        
        result = {
            'username': data['username'],
            'password': decrypted_password
        }
        # Include garth OAuth2 tokens if available (decrypt first)
        if 'garth_tokens_encrypted' in data:
            try:
                from encryption_helper import decrypt_password
                import json as _json
                result['garth_tokens'] = _json.loads(decrypt_password(data['garth_tokens_encrypted']))
            except Exception as te:
                print(f"Could not decrypt garth tokens: {te}")
        return result
        
    except Exception as e:
        print(f"Firestore Error (get_garmin_credentials): {e}")
        return None


def delete_garmin_credentials(user_id: str) -> bool:
    """
    Deletes Garmin credentials (GDPR compliance / user disconnect).
    
    Args:
        user_id: Firebase UID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        doc_ref = db.collection('users').document(user_id).collection('garmin_credentials').document('default')
        doc_ref.delete()
        print(f"[DELETED] Garmin credentials deleted for user: {user_id}")
        return True
        
    except Exception as e:
        print(f"Firestore Error (delete_garmin_credentials): {e}")
        return False


def save_garmin_tokens(user_id: str, tokens: dict) -> bool:
    """
    Saves garth OAuth2 tokens to Firestore alongside credentials.
    Called after successful fresh login to avoid re-login on next sync.
    
    Args:
        user_id: Firebase UID
        tokens: garth OAuth2 token dict (from oauth2_token.json)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from encryption_helper import encrypt_password
        import json
        doc_ref = db.collection('users').document(user_id).collection('garmin_credentials').document('default')
        # Encrypt tokens as JSON string before storing
        encrypted_tokens = encrypt_password(json.dumps(tokens))
        doc_ref.update({
            'garth_tokens_encrypted': encrypted_tokens,
            'tokens_updated_at': firestore.SERVER_TIMESTAMP
        })
        print(f"[SUCCESS] Garth tokens saved (encrypted) for user: {user_id}")
        return True
    except Exception as e:
        print(f"Firestore Error (save_garmin_tokens): {e}")
        return False


def check_garmin_credentials_exist(user_id: str) -> bool:
    """
    Checks if user has saved Garmin credentials.
    
    Args:
        user_id: Firebase UID
        
    Returns:
        True if credentials exist, False otherwise
    """
    try:
        doc_ref = db.collection('users').document(user_id).collection('garmin_credentials').document('default')
        return doc_ref.get().exists
    except Exception as e:
        print(f"Firestore Error (check_garmin_credentials_exist): {e}")
        return False

"""
Firestore manager functions for Garmin daily metrics (per-user storage).
Part of CSV migration (Phase 10.3 - Multi-User Data Isolation).
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import firestore_manager

# Use shared Firestore client
db = firestore_manager.db
firestore = firestore_manager.firestore

def save_daily_metric(user_id: str, date_str: str, metric_data: dict) -> bool:
    """
    Save or update a daily health metric to Firestore.
    
    Schema: garmin_metrics/{user_id}/daily_metrics/{date}
    
    Args:
        user_id: Firebase UID
        date_str: Date in YYYY-MM-DD format
        metric_data: Dict containing daily metrics (HRV, stress, sleep, etc.)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure user_id is set
        metric_data['user_id'] = user_id
        metric_data['date'] = date_str
        metric_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        # If this is first save, add created_at
        doc_ref = db.collection('garmin_metrics').document(user_id)\
                    .collection('daily_metrics').document(date_str)
        
        if not doc_ref.get().exists:
            metric_data['created_at'] = firestore.SERVER_TIMESTAMP
        
        doc_ref.set(metric_data, merge=True)
        return True
        
    except Exception as e:
        print(f"Firestore Error (save_daily_metric): {e}")
        return False


def get_user_daily_metrics(user_id: str, days: int = 30) -> List[Dict]:
    """
    Get last N days of metrics for a specific user.
    
    Args:
        user_id: Firebase UID
        days: Number of days to retrieve (default 30)
    
    Returns:
        List of metric dictionaries, ordered by date (oldest first)
    """
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        docs = db.collection('garmin_metrics').document(user_id)\
                 .collection('daily_metrics')\
                 .where('date', '>=', start_date.isoformat())\
                 .where('date', '<=', end_date.isoformat())\
                 .order_by('date').stream()
        
        metrics = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            metrics.append(data)
        
        return metrics
        
    except Exception as e:
        print(f"Firestore Error (get_user_daily_metrics): {e}")
        return []


def get_metrics_in_range(user_id: str, start_date: str, end_date: str) -> List[Dict]:
    """
    Get metrics within a specific date range.
    
    Args:
        user_id: Firebase UID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        List of metric dictionaries within the specified range
    """
    try:
        docs = db.collection('garmin_metrics').document(user_id)\
                 .collection('daily_metrics')\
                 .where('date', '>=', start_date)\
                 .where('date', '<=', end_date)\
                 .order_by('date').stream()
        
        metrics = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            metrics.append(data)
        
        return metrics
        
    except Exception as e:
        print(f"Firestore Error (get_metrics_in_range): {e}")
        return []


def get_user_metrics_count(user_id: str) -> int:
    """
    Get total number of daily metric documents for a user.
    
    Args:
        user_id: Firebase UID
    
    Returns:
        Count of metric documents
    """
    try:
        docs = db.collection('garmin_metrics').document(user_id)\
                 .collection('daily_metrics').stream()
        
        count = sum(1 for _ in docs)
        return count
        
    except Exception as e:
        print(f"Firestore Error (get_user_metrics_count): {e}")
        return 0


def get_latest_metric(user_id: str) -> Optional[Dict]:
    """
    Get the most recent daily metric for a user.
    
    Args:
        user_id: Firebase UID
    
    Returns:
        Latest metric dictionary or None if no metrics found
    """
    try:
        docs = db.collection('garmin_metrics').document(user_id)\
                 .collection('daily_metrics')\
                 .order_by('date', direction=firestore.Query.DESCENDING)\
                 .limit(1).stream()
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        
        return None
        
    except Exception as e:
        print(f"Firestore Error (get_latest_metric): {e}")
        return None


def delete_user_metrics(user_id: str) -> bool:
    """
    Delete all metrics for a user (GDPR compliance).
    
    Args:
        user_id: Firebase UID
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get all metric documents
        docs = db.collection('garmin_metrics').document(user_id)\
                 .collection('daily_metrics').stream()
        
        # Batch delete
        batch = db.batch()
        count = 0
        
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            
            # Commit in batches of 400 (Firestore limit is 500)
            if count >= 400:
                batch.commit()
                batch = db.batch()
                count = 0
        
        # Final commit
        if count > 0:
            batch.commit()
        
        # Delete parent document
        db.collection('garmin_metrics').document(user_id).delete()
        
        print(f"Deleted {count} metric documents for user {user_id}")
        return True
        
    except Exception as e:
        print(f"Firestore Error (delete_user_metrics): {e}")
        return False


def batch_save_metrics(user_id: str, metrics_list: List[Dict]) -> bool:
    """
    Batch save multiple metrics efficiently.
    
    Args:
        user_id: Firebase UID
        metrics_list: List of metric dictionaries (each must have 'date' field)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        batch = db.batch()
        count = 0
        
        for metric in metrics_list:
            date_str = metric.get('date')
            if not date_str:
                continue
            
            metric['user_id'] = user_id
            metric['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = db.collection('garmin_metrics').document(user_id)\
                        .collection('daily_metrics').document(date_str)
            
            batch.set(doc_ref, metric, merge=True)
            count += 1
            
            # Commit in batches of 400
            if count >= 400:
                batch.commit()
                batch = db.batch()
                count = 0
        
        # Final commit
        if count > 0:
            batch.commit()
        
        print(f"Batch saved {len(metrics_list)} metrics for user {user_id}")
        return True
        
    except Exception as e:
        print(f"Firestore Error (batch_save_metrics): {e}")
        return False


def log_security_event(event_type: str, data: dict) -> bool:
    """
    Logs a security event (e.g., rate limit exceeded, auth failure) to Firestore.
    
    Args:
        event_type: Type of event (e.g., "rate_limit_exceeded")
        data: Dict containing event details (IP, path, etc.)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        event_data = {
            "event_type": event_type,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "data": data
        }
        db.collection('security_events').add(event_data)
        return True
    except Exception as e:
        print(f"Firestore Error (log_security_event): {e}")
        return False

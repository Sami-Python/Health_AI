from fastapi import FastAPI, HTTPException, Request
from firebase_admin import auth
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional
import firestore_manager as db_manager # Alias to keep code changes minimal
# REMOVED: import db_manager as local_db # DuckDB for history/analytics (Phase 7 Migration)
from fastapi import Depends
from auth_middleware import verify_token, verify_admin
import json
import ai_coach

from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
from datetime import date, timedelta, datetime
import calendar

limiter = Limiter(key_func=get_remote_address)

# Enhanced API metadata
app = FastAPI(
    title="Health AI Coach API",
    version="1.0.0",
    description="""
🏃 **Health AI Coach** - Your personal AI-powered endurance training assistant.

## Features

* **Goal Management**: Create, track, and manage training goals
* **AI Insights**: Get personalized training recommendations powered by Google Gemini
* **Garmin Integration**: Securely connect and sync Garmin data
* **Training Calendar**: Plan and track workouts
* **Analytics**: Visualize recovery metrics and training load

## Authentication

All endpoints (except `/health`) require Firebase Authentication.  
Include the ID token in the `Authorization` header:

```
Authorization: Bearer <your-firebase-id-token>
```

## Rate Limiting

- Most endpoints: 20 requests/minute
- AI endpoints: 10 requests/minute  
- Garmin credentials: 5 requests/hour

## Data Security

- All passwords encrypted with AES-256
- Row-level security (user_id filtering)
- GDPR compliant data export
""",
    contact={
        "name": "Health AI Support",
        "url": "https://github.com/yourusername/health_ai",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/metrics/history", tags=["Analytics"])
async def get_metrics_history(user: dict = Depends(verify_token)):
    """
    Get historical recovery and training metrics.
    
    Returns time-series data for:
    - Sleep quality and duration
    - Body Battery / Readiness scores
    - Heart Rate Variability (HRV)
    - Training load and stress
    
    **Data Source:** Garmin CSV export (processed historical data)
    
    **Use Case:** Powering charts and sparklines in the dashboard
    
    **Example Response:**
    ```json
    [
        {
            "date": "2024-01-15",
            "sleep_score": 85,
            "body_battery": 78,
            "hrv": 65,
            "training_load": 120
        }
    ]
    ```
    
    **Note:** Limited to last 90 days of data for performance.
    """
    try:
        # Load data from CSV (Migration Phase: Using CSV as SSOT for history)
        csv_path = "../Health_AI/data/garmin_merged_features.csv"
        
        # Check if running in Docker (path might differ)
        if not os.path.exists(csv_path):
             csv_path = "/data/Health_AI/data/garmin_merged_features.csv"
             
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"History CSV not found at {csv_path}")

        df = pd.read_csv(csv_path)
        
        # Ensure date column
        if 'calendarDate' in df.columns:
             df['date'] = pd.to_datetime(df['calendarDate'])
        else:
             df['date'] = pd.to_datetime(df['date'])
             
        df = df.sort_values('date')
        
        # --- CTL / ATL / TSB Calculations ---
        # 1. Define Load Proxy
        # workout_calories is best for Training Load. If NaN, assume 0 (Rest Day).
        if 'workout_calories' in df.columns:
             df['load'] = df['workout_calories'].fillna(0)
        elif 'activeKilocalories' in df.columns:
             df['load'] = df['activeKilocalories'].fillna(0)
        else:
             df['load'] = 0
             
        # 2. Daily Load moving averages
        # ATL = 7 days, CTL = 42 days, TSB = CTL - ATL
        df['ATL'] = df['load'].rolling(window=7, min_periods=1).mean()
        df['CTL'] = df['load'].rolling(window=42, min_periods=1).mean()
        df['TSB'] = df['CTL'] - df['ATL']
        
        # --- Recovery Metrics ---
        # Ensure columns exist
        if 'bodyBatteryHighestValue' not in df.columns:
            df['bodyBatteryHighestValue'] = 0
        if 'totalSleep_minutes' not in df.columns:
             df['totalSleep_minutes'] = 0
             
        # Select last 30 days for frontend
        recent = df.tail(30).copy()
        
        result = []
        for _, row in recent.iterrows():
            result.append({
                "date": row['date'].strftime('%Y-%m-%d'),
                "ctl": round(row['CTL'], 1),
                "atl": round(row['ATL'], 1),
                "tsb": round(row['TSB'], 1),
                "load": int(row['load']),
                "readiness": int(row['bodyBatteryHighestValue']),
                "sleep_min": int(row['totalSleep_minutes'])
            })
            
        return result

    except Exception as e:
        print(f"Metrics Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/")
@limiter.limit("5/minute")
def read_root(request: Request):
    return {"message": "Health AI API is running! (DuckDB Version)"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/goals", tags=["Goals"])
@limiter.limit("10/minute")
def get_goals(request: Request, user: dict = Depends(verify_token)):
    """
    Get all active goals for the authenticated user.
    
    Returns a list of goals with calculated progress based on:
    - Garmin activity data (CSV)
    - Manual workout logs (Firestore)
    
    **Goal Types:**
    - `weekly`: Recurring weekly goals (e.g., 50km/week)
    - `monthly`: Recurring monthly goals
    - `target_date`: One-time goals with deadline
    - `race`: Race preparation goals
    
    **Progress Calculation:**
    - Weekly/Monthly: Current period progress
    - Target Date/Race: Total progress since creation
    
    **Example Response:**
    ```json
    [
        {
            "id": "goal123",
            "activity_type": "Running",
            "target_value": 50,
            "target_unit": "km",
            "period_type": "weekly",
            "status": "ACTIVE",
            "current_value": 32.5,
            "progress_percentage": 65,
            "remaining": 17.5,
            "days_left": 3
        }
    ]
    ```
    
    **Rate Limit:** 10 requests/minute
    """
    try:
        raw_goals = db_manager.get_active_goals(user['uid'])
        
        # Enrich with progress
        enriched_goals = []
        for g in raw_goals:
            progress = calculate_goal_progress(user['uid'], g)
            g.update(progress)
            enriched_goals.append(g)
            
        return enriched_goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_goal_progress(user_id: str, goal: dict):
    """
    Calculates current progress for a goal based on:
    1. Garmin Data (CSV)
    2. Manual Logs (Firestore 'workouts')
    """
    try:
        target_val = float(goal.get('target_value', 0))
        activity_type = goal.get('activity_type', '').lower()
        period = goal.get('period_type', 'weekly')
        
        # 1. Determine Date Range
        today = date.today()
        start_date = today
        end_date = today
        
        if period == 'weekly':
            # Monday to Sunday
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'monthly':
            # 1st to End of Month
            start_date = today.replace(day=1)
            # End of month approach
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
        elif period == 'target_date' or period == 'race':
            # Range: From Creation (or fallback) to Target Date
            target_date_str = goal.get('target_date')
            if target_date_str:
                end_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            else:
                 end_date = today + timedelta(days=30) # Fallback

            # Start from creation or if missing, assume "Start of Year" or reasonable fallback
            created_at = goal.get('created_at')
            if created_at:
                if isinstance(created_at, datetime):
                     start_date = created_at.date()
                elif isinstance(created_at, str):
                     try:
                         # Handle Firestore timestamp string or isoformat
                         start_date = datetime.fromisoformat(created_at).date()
                     except:
                         start_date = datetime(2025, 1, 1).date()
                else:
                    # Firestore Timestamp object?
                    try:
                        start_date = created_at.date()
                    except:
                        start_date = datetime(2025, 1, 1).date()
            else:
                # If no creation date, fallback to start of current year or user "start"
                # For this MVP, let's use 2025-01-01 as hard start for legacy data
                start_date = datetime(2025, 1, 1).date()

        if period == 'race':
            # Race Mode: Calculate countdown
            if not end_date:
                # If no target date, invalid race config
                return {"days_remaining": 0, "current_value": 0, "progress_percentage": 0}
            
            # Days remaining = Target Date - Today
            delta = end_date - today
            days_remaining = max(0, delta.days)
            
            return {
                "current_value": days_remaining, 
                "days_remaining": days_remaining,
                "progress_percentage": 0 
            }


        # 2. Get Data Sources
        total_value = 0.0
        
        # A) Garmin CSV (History)
        # We need to read CSV. It's not efficient to read on every request loop, 
        # but for < 10 goals it's acceptable for MVP.
        # Ideally cache the DF.
        csv_path = "../Health_AI/data/garmin_merged_features.csv"
        if not os.path.exists(csv_path):
             csv_path = "/data/Health_AI/data/garmin_merged_features.csv"
        
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                if 'calendarDate' in df.columns:
                     df['date'] = pd.to_datetime(df['calendarDate']).dt.date
                elif 'date' in df.columns:
                     df['date'] = pd.to_datetime(df['date']).dt.date
                
                # Filter Date
                mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                filtered = df.loc[mask]
                
                # Filter Activity? Garmin CSV might not have 'activity type' per row if it's daily summary.
                # If the CSV is "Daily Summaries", it aggregates ALL activities.
                # We can't distinguish "Running" vs "Cycling" easily from daily summary CSV 
                # unless we have specific columns like 'runningDistance'.
                # For this MVP, if goal is 'Running' and we only have 'totalDistance', it might be inaccurate.
                # Let's check columns for 'distanceInMeters' (General).
                # If target_unit is 'km', use distance. If 'h' or 'min', use duration.
                
                if goal.get('target_unit') in ['km', 'm']:
                    if 'totalDistanceOnFoot' in filtered.columns: # Specific to walking/running
                         total_value += filtered['totalDistanceOnFoot'].sum() / 1000.0 # meters to km
                    elif 'distanceInMeters' in filtered.columns:
                         total_value += filtered['distanceInMeters'].sum() / 1000.0
                elif goal.get('target_unit') in ['h', 'min']:
                     if 'activeSeconds' in filtered.columns: # activeSeconds or similar
                         seconds = filtered['activeSeconds'].sum()
                         if goal.get('target_unit') == 'h':
                             total_value += seconds / 3600.0
                         else:
                             total_value += seconds / 60.0

            except Exception as csv_e:
                print(f"Goal Calc CSV Error: {csv_e}")

        # B) Manual Workouts (Firestore)
        # Get workouts in range
        manual_workouts = db_manager.get_workouts_in_range(user_id, start_date.isoformat(), end_date.isoformat())
        for w in manual_workouts:
            # Filter Activity
            # Fuzzy match: "Run" in "Running"
            w_activity = w.get('activity', '').lower()
            if activity_type in w_activity or w_activity in activity_type:
                 # Check unit
                 if goal.get('target_unit') in ['min', 'h']:
                     duration = w.get('duration_min', 0)
                     if goal.get('target_unit') == 'h':
                         total_value += duration / 60.0
                     else:
                         total_value += duration
                 elif goal.get('target_unit') in ['km']:
                      # We don't store distance in manual workout currently (only duration/rpe)
                      # fallback: estimate? or 0.
                      pass

        return {
            "current_value": round(total_value, 1),
            "progress_percentage": min(100, int((total_value / target_val) * 100)) if target_val > 0 else 0
        }

    except Exception as e:
        print(f"Goal Calc Error: {e}")
        return {"current_value": 0, "progress_percentage": 0}

class GoalCreate(BaseModel):
    activity_type: str
    target_value: float
    target_unit: str
    period_type: str # 'weekly', 'monthly', 'target_date'
    frequency: Optional[str] = None # kept for backward compatibility or extra info
    target_date: Optional[str] = None # ISO format date string YYYY-MM-DD
    description: Optional[str] = None

class UserProfile(BaseModel):
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    gender: Optional[str] = None
    resting_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None


@app.post("/goals", tags=["Goals"])
@limiter.limit("5/minute")
def create_goal(goal: GoalCreate, request: Request, user: dict = Depends(verify_token)):
    """
    Create a new training goal.
    
    **Request Body:**
    - `activity_type`: "Running", "Cycling", "Swimming", etc.
    - `target_value`: Numeric goal (e.g., 50 for 50km)
    - `target_unit`: "km", "min", "hours", "times", "kcal", "kg"
    - `period_type`: "weekly", "monthly", "target_date", "race"
    - `frequency`: "Weekly" or "Monthly" (for recurring goals)
    - `target_date`: ISO date string (for target_date/race goals)
    - `description`: Optional text description
    
    **Example Request:**
    ```json
    {
        "activity_type": "Running",
        "target_value": 50,
        "target_unit": "km",
        "period_type": "weekly",
        "frequency": "Weekly",
        "description": "Marathon preparation"
    }
    ```
    
    **Rate Limit:** 5 requests/minute
    """
    try:
        success = db_manager.add_goal(user['uid'], goal.model_dump())
        if success:
            return {"status": "success", "message": "Goal added"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add goal")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/goals/{goal_id}", tags=["Goals"])
async def delete_goal_endpoint(goal_id: str, user: dict = Depends(verify_token)):
    """
    Delete a specific goal.
    
    **Path Parameters:**
    - `goal_id`: Firestore document ID of the goal
    
    **Response:**
    - `200`: Goal deleted successfully
    - `404`: Goal not found or access denied
    
    **Note:** Only the goal owner can delete their own goals (enforced by user_id check).
    """
    try:
        if db_manager.delete_goal(user['uid'], goal_id):
            return {"status": "success", "message": "Goal deleted"}
        else:
            raise HTTPException(status_code=404, detail="Goal not found or access denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/goals/{goal_id}", tags=["Goals"])
async def update_goal_endpoint(goal_id: str, goal: GoalCreate, user: dict = Depends(verify_token)):
    """
    Update an existing goal.
    
    **Path Parameters:**
    - `goal_id`: Firestore document ID of the goal to update
    
    **Request Body:** Same as POST (all fields)
    
    **Use Case:** Edit target values, change goal type, update description
    
    **Response:**
    - `200`: Goal updated successfully  
    - `404`: Goal not found or access denied
    """
    try:
        updates = {
            "activity_type": goal.activity_type,
            "target_value": goal.target_value,
            "target_unit": goal.target_unit,
            "period_type": goal.period_type,
            "frequency": goal.frequency,
            "target_date": goal.target_date,
            "description": goal.description
        }
        if db_manager.update_goal(user['uid'], goal_id, updates):
            return {"status": "success", "message": "Goal updated"}
        else:
            raise HTTPException(status_code=404, detail="Goal not found or access denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profile", tags=["User"])
@limiter.limit("20/minute")
async def get_profile_endpoint(request: Request, user: dict = Depends(verify_token)):
    """
    Get the authenticated user's physical profile.
    
    Returns details like:
    - Age, weight, height
    - Heart rate zones (resting/max)
    - Gender
    
    Data is stored in the `users` collection in Firestore.
    """
    try:
        profile = db_manager.get_user_profile(user['uid'])
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/profile", tags=["User"])
@limiter.limit("10/minute")
async def update_profile_endpoint(profile: UserProfile, request: Request, user: dict = Depends(verify_token)):
    """
    Update the user's physical profile.
    
    Allows partial updates of physical and physiological metrics.
    """
    try:
        # Filter out None values to allow partial updates (though frontend sends all)
        data = {k: v for k, v in profile.model_dump().items() if v is not None}
        
        if db_manager.update_user_profile(user['uid'], data):
            return {"status": "success", "message": "Profile updated"}
        else:
             raise HTTPException(status_code=500, detail="Failed to update profile")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.delete("/account", tags=["User"])
@limiter.limit("2/minute")
async def delete_account_endpoint(request: Request, user: dict = Depends(verify_token)):
    """
    Permanently delete the user account and all associated data.
    
    **CRITICAL:** This action is irreversible. It deletes:
    1. All Firestore documents (goals, workouts, plans, profile)
    2. The Firebase Authentication user record
    
    Complies with GDPR "Right to Erasure".
    """
    try:
        uid = user['uid']
        
        # 1. Delete Firestore Data
        if not db_manager.delete_all_user_data(uid):
             raise HTTPException(status_code=500, detail="Failed to delete user data")

        # 2. Delete Auth User
        try:
            auth.delete_user(uid)
        except Exception as auth_error:
            print(f"Auth Deletion Error: {auth_error}")
            raise HTTPException(status_code=500, detail="Failed to delete authentication user")

        return {"status": "success", "message": "Account deleted permanently"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- GDPR Compliance Endpoints (Phase 7.2) ---

@app.get("/user/export")
@limiter.limit("3/hour")
async def export_user_data(request: Request, user: dict = Depends(verify_token)):
    """
    Exports all user data as JSON (GDPR compliance).
    Includes: goals, workouts, plans, profile
    """
    try:
        uid = user['uid']
        
        # Aggregate all user data
        export_data = {
            "user_id": uid,
            "exported_at": datetime.now().isoformat(),
            "goals": db_manager.get_all_goals(uid),
            "workouts": db_manager.get_all_workouts(uid, limit=1000),
            "plans": db_manager.get_recent_plans(uid, limit=100),
            "profile": db_manager.get_user_profile(uid)
        }
        
        # Return as JSON with download header
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f"attachment; filename=health_ai_data_{uid}.json"
            }
        )
    except Exception as e:
        print(f"Export Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class FeedbackSubmission(BaseModel):
    category: str  # "bug", "feature_request", "general"
    message: str
    page: Optional[str] = None  # Which page user was on

@app.post("/feedback")
@limiter.limit("5/hour")
async def submit_feedback(
    feedback: FeedbackSubmission, 
    request: Request, 
    user: dict = Depends(verify_token)
):
    """Collects user feedback (bugs, feature requests, general comments)."""
    try:
        feedback_doc = {
            "user_id": user['uid'],
            "category": feedback.category,
            "message": feedback.message,
            "page": feedback.page,
        }
        
        if db_manager.save_feedback(user['uid'], feedback_doc):
            return {"status": "success", "message": "Feedback received. Thank you!"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save feedback")
    except Exception as e:
        print(f"Feedback Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Admin Endpoints ---

@app.get("/admin/feedback")
@limiter.limit("20/minute")
async def get_all_feedback_admin(
    request: Request,
    user: dict = Depends(verify_admin),
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100
):
    """
    Admin endpoint: Returns all user feedback.
    Optional filters: status, category
    """
    try:
        # Simple admin check: you can enhance this by checking user role in Firestore
        # For now, any authenticated user can access (you can restrict to specific UIDs)
        
        all_feedback = db_manager.get_all_feedback(limit=limit)
        
        # Apply filters if provided
        filtered = all_feedback
        if status:
            filtered = [f for f in filtered if f.get('status') == status]
        if category:
            filtered = [f for f in filtered if f.get('category') == category]
        
        return {
            "total": len(filtered),
            "feedback": filtered
        }
    except Exception as e:
        print(f"Admin Feedback Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ... existing code ...

@app.get("/next-workout", tags=["Workouts"])
@limiter.limit("20/minute")
def get_next_workout_endpoint(request: Request, user: dict = Depends(verify_token)):
    """
    Retrieve the next planned workout for the user.
    
    Returns the soonest 'PENDING' workout where date >= today.
    """
    try:
        # Use Firestore for next workout (Logic Updated in firestore_manager.py)
        workout = db_manager.get_next_workout(user['uid'])
        if not workout:
            return {} # Frontend expects empty object or specific null handling?
            # Looking at frontend: `value={nextWorkout?.content?.activity || "Rest Day"}`. 
            # If {} returned, nextWorkout is {}, optional chaining works.
        return workout
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workouts/weekly-status", tags=["Analytics"])
async def get_weekly_status(user: dict = Depends(verify_token)):
    """
    Get the summary of training load for the current week.
    
    Calculates:
    - `current_load`: Sum of load from completed (DONE) workouts
    - `planned_load`: Sum of load from pending (PENDING) workouts
    - `breakdown`: Daily breakdown of the weekly load
    """
    # Migrated to Firestore
    current, planned, breakdown = db_manager.get_weekly_load_status(user['uid'])
    return {
        "current_load": current,
        "planned_load": planned,
        "breakdown": breakdown
    }

@app.get("/workouts/upcoming", tags=["Workouts"])
@limiter.limit("20/minute")
def get_upcoming_workouts(request: Request, user: dict = Depends(verify_token)):
    """
    Get all future planned workouts.
    
    Used by the Training Calendar to display upcoming sessions.
    """
    try:
        return db_manager.get_upcoming_workouts(user['uid'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Migration Endpoints (Streamlit Features) ---

class ManualWorkout(BaseModel):
    date: str
    activity: str
    duration_min: int
    rpe: int
    notes: Optional[str] = ""

@app.post("/workouts/manual", tags=["Workouts"])
async def log_manual_workout(workout: ManualWorkout, user: dict = Depends(verify_token)):
    """
    Log a workout manually (e.g., gym session or sport not tracked by Garmin).
    
    **Fields:**
    - `date`: ISO format (YYYY-MM-DD)
    - `activity`: Activity name
    - `duration_min`: Duration in minutes
    - `rpe`: Rate of Perceived Exertion (1-10)
    - `notes`: Optional description
    """
    try:
        # Pydantic validates date string format if we used date type, but here it's string.
        # Ensure date format
        from datetime import date, datetime
        date_obj = date.fromisoformat(workout.date)
        
        # Map to Firestore document structure (Pure Firestore - Phase 7 Migration)
        workout_doc = {
            "date": workout.date, # YYYY-MM-DD
            "activity": workout.activity,
            "duration_min": workout.duration_min,
            "rpe": workout.rpe,
            "description": workout.notes,
            "status": "DONE",
            "source": "MANUAL",
            "load_estimate": workout.duration_min * workout.rpe, # Simple load proxy
            "structure": "Manual Log"
        }
        db_manager.save_workout(user['uid'], workout_doc)

        return {"status": "success", "message": "Workout logged successfully"}
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format (YYYY-MM-DD required)")
    except Exception as e:
        print(f"Error logging manual workout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/refresh")
async def refresh_data(user: dict = Depends(verify_token)):
    """
    Triggers Garmin data fetch and model retraining for the authenticated user.
    
    NEW: Now uses per-user Garmin credentials from Firestore.
    Falls back to legacy mode if user has no credentials saved.
    """
    try:
        import sys
        import os
        import importlib
        

        # Determine path to scripts (supporting Docker /app vs Local /backend)
        # Using fixed structure now: backend/scripts
        
        # We are in backend/main.py. scripts are in ./scripts
        script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
        
        if not os.path.exists(os.path.join(script_dir, "fetch_garmin_data.py")):
             raise FileNotFoundError(f"Could not locate fetch_garmin_data.py in {script_dir}")

        # Add scripts to path so we can import them
        if script_dir not in sys.path:
            sys.path.append(script_dir)
            
        # Change CWD to project root (../) so that scripts finding "Health_AI/data" works
        # Current file: .../backend/main.py
        # Root: .../
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)
        
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            import fetch_garmin_data
            import process_garmin_data
            
            # Force reload to ensure fresh execution
            importlib.reload(fetch_garmin_data)
            importlib.reload(process_garmin_data)
            
            # Run Fetch with user_id (NEW: Per-user credentials)
            uid = user['uid']
            print(f"Starting Data Fetch for user: {uid}...")
            
            # Check if user has Garmin credentials
            has_credentials = db_manager.check_garmin_credentials_exist(uid)
            
            if has_credentials:
                print(f"✅ User has Garmin credentials, fetching with per-user mode")
                fetch_garmin_data.main(user_id=uid)
            else:
                print(f"⚠️  User has no Garmin credentials, attempting legacy mode")
                # Try legacy mode (falls back to GARMIN_EMAIL/PASSWORD from .env)
                fetch_garmin_data.main(user_id=None)
            
            # Run Process
            print("Starting Model Training...")
            process_garmin_data.main_process()
            print("✅ Model Training completed successfully.")
            
        except Exception as script_error:
            print(f"❌ Error during script execution: {script_error}")
            import traceback
            traceback.print_exc()
            raise script_error
        finally:
            # Always restore CWD to avoid side effects
            os.chdir(original_cwd)
        
        return {"status": "success", "message": "Data refreshed and model retrained."}
        
    except ValueError as ve:
        # Credentials error
        print(f"Credentials error: {ve}")
        raise HTTPException(
            status_code=400, 
            detail=str(ve) + " Please connect your Garmin account in Profile settings."
        )
    except Exception as e:
        print(f"Refresh error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@app.get("/ai/insight", tags=["AI"])
@limiter.limit("10/minute")
async def get_ai_insight(request: Request, user: dict = Depends(verify_token)):
    """
    Generate AI-powered daily training insight.
    
    Analyzes user's recovery metrics and provides personalized recommendations using Google Gemini 2.5.
    
    **Data Sources:**
    - Latest recovery metrics (TSB, Readiness, Sleep, CTL)
    - Garmin historical data
    - Training goals
    
    **Caching:**
    - Results cached for 24 hours (per user, per day)
    - Reduces API costs and improves response time
    - Cache stored in Firestore (`daily_insights` collection)
    
    **AI Model:** Google Gemini 2.5 Flash
    
    **Example Response:**
    ```json
    {
        "insight": "Your recovery is excellent today (Readiness: 85%). Consider a moderate intensity run of 8-10km. Your training load is optimal for race preparation.",
        "cached": true,
        "generated_at": "2024-01-15T08:00:00Z"
    }
    ```
    
    **Rate Limit:** 10 requests/minute
    
    **Fallback:** Returns generic advice if AI generation fails
    """
    try:
        # Reuse logic to get latest 30 days, but we only need the last one
        metrics = await get_metrics_history(user)
        if not metrics or len(metrics) == 0:
            return {"insight": "Ei tarpeeksi dataa analyysiin."}
            
        latest = metrics[-1] # Last day
        
        # 1. OPTIMIZATION: Check Cache
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        cached_insight = db_manager.get_daily_insight(user['uid'], today_str)
        
        if cached_insight:
            return {"insight": cached_insight}
        
        # Prepare context for AI
        ctx = {
            "tsb": latest['tsb'],
            "readiness": latest['readiness'],
            "sleep_min": latest['sleep_min'],
            "ctl": latest['ctl']
        }
        
        insight = ai_coach.generate_daily_insight(ctx)
        
        # 2. OPTIMIZATION: Save to Cache
        if insight and "Error" not in insight:
            db_manager.save_daily_insight(user['uid'], today_str, insight)
            
        return {"insight": insight}
        
    except Exception as e:
        print(f"Insight Endpoint Error: {e}")
        return {"insight": "Tänään kannattaa kuunnella kehoa."} # Fallback


@app.get("/ai/model-metrics")
async def get_model_metrics(user: dict = Depends(verify_token)):
    try:
        # Paths
        metrics_path = os.path.join(os.path.dirname(__file__), "data", "model_metrics.json")
        fi_path = os.path.join(os.path.dirname(__file__), "..", "feature_importance.json")
        
        # Docker paths
        if os.path.exists("/app/data/model_metrics.json"):
            metrics_path = "/app/data/model_metrics.json"
        if os.path.exists("/feature_importance.json"):
            fi_path = "/feature_importance.json"
        
        data = {"r2": 0, "mae": 0, "last_trained": "Never", "top_features": {}, "data_points": 0}
        
        # 0. Get Data Volume
        # Try finding the CSV to get accurate data point count
        csv_path = os.path.join(os.path.dirname(__file__), "..", "Health_AI", "data", "garmin_merged_features.csv")
        if not os.path.exists(csv_path):
             csv_path = "/Health_AI/data/garmin_merged_features.csv" # Docker fallback
             
        if os.path.exists(csv_path):
             try:
                 df = pd.read_csv(csv_path)
                 data['data_points'] = len(df)
             except:
                 pass

        # 1. Load Metrics
        try:
            if os.path.exists(metrics_path):
                with open(metrics_path, "r") as f:
                    data.update(json.load(f))
        except Exception as e:
            print(f"Error loading metrics: {e}")
            
        # 2. Load Feature Importance
        try:
            if os.path.exists(fi_path):
                with open(fi_path, "r") as f:
                    fi_data = json.load(f)
                    # Filter top 10 and ensure float values
                    sorted_fi = dict(sorted(fi_data.items(), key=lambda item: item[1], reverse=True)[:10])
                    data['top_features'] = sorted_fi
        except Exception as e:
            print(f"Error loading feature importance: {e}")
            
        return data
    except Exception as e:
        print(f"Error fetching model metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PlanGenerationRequest(BaseModel):
    days: int = 1
    rejected_plan_details: Optional[dict] = None

@app.post("/plans/generate")
@limiter.limit("5/minute")
async def generate_plan_endpoint(request: Request, req: PlanGenerationRequest, user: dict = Depends(verify_token)):
    # Check Daily Limit
    if not db_manager.check_daily_generation_limit(user['uid']):
         raise HTTPException(status_code=429, detail="Daily plan generation limit (5) reached.")
    try:
        # 1. Get Context (Metrics)
        metrics = await get_metrics_history(user)
        if not metrics or len(metrics) == 0:
            latest = {"tsb": 0, "readiness": 50, "sleep_min": 420, "ctl": 0, "load": 0}
        else:
            latest = metrics[-1]

        ctx = {
            "date": date.today().isoformat(),
            "predicted_charge": latest.get('readiness', 50),
            "sleep_hours": latest.get('sleep_min', 0) / 60,
            "recent_load": latest.get('load', 0),
            "ctl": latest.get('ctl', 0),
            "tsb": latest.get('tsb', 0)
        }

        # 2. Call AI Coach
        response_json = ai_coach.generate_coach_advice(
            user_id=user['uid'],
            context=ctx,
            n_days=req.days,
            rejected_context=req.rejected_plan_details
        )
        
        # 3. Parse and Save
        import json
        from datetime import datetime, timedelta
        
        try:
            cleaned = response_json.replace('```json', '').replace('```', '').strip()
            plans = json.loads(cleaned)
            
            today = date.today()
            
            # 3b. Overwrite Logic: Delete existing PENDING workouts for the target range
            max_day = 1
            for p in plans:
                max_day = max(max_day, p.get('day', 1))
                
            end_date_obj = today + timedelta(days=max_day-1)
            
            db_manager.delete_pending_workouts(
                user['uid'], 
                today.isoformat(), 
                end_date_obj.isoformat()
            )

            saved_count = 0
            for p in plans:
                day_offset = p.get('day', 1) - 1
                workout_date = today + timedelta(days=day_offset)
                
                workout_doc = {
                    "date": workout_date.isoformat(),
                    "activity": p.get('activity', 'Rest'),
                    "description": p.get('description', ''),
                    "duration_min": p.get('duration_min', 0),
                    "load_estimate": p.get('load_estimate', 0),
                    "structure": p.get('structure_summary', ''),
                    "details": p.get('detailed_steps', []),
                    "tips": p.get('tips', ''),
                    "status": "PENDING",
                    "source": "AI_GENERATED"
                }
                
                db_manager.save_workout(user['uid'], workout_doc)
                saved_count += 1

            # 4. Save History Log
            activity_counts = {}
            for p in plans:
                act = p.get('activity', 'Other')
                activity_counts[act] = activity_counts.get(act, 0) + 1
                
            summary_text = f"Plan ({req.days} days): " + ", ".join([f"{count}x {act}" for act, count in activity_counts.items()])

            db_manager.save_generated_plan(
                user['uid'],
                {"raw_json": plans},
                summary_text,
                ctx['predicted_charge']
            )
            
            return {"status": "success", "count": saved_count, "plans": plans}

        except Exception as parse_error:
            print(f"AI Parse Error: {parse_error} \nResponse: {response_json}")
            if "QUOTA_EXCEEDED" in str(response_json):
                 raise HTTPException(status_code=429, detail="AI Quota Exceeded. Please try again later.")
            raise HTTPException(status_code=500, detail="Failed to parse AI response")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Plan Gen Error: {e}")
        if "QUOTA_EXCEEDED" in str(e):
             raise HTTPException(status_code=429, detail="AI Quota Exceeded. Please try again later.")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/workouts/{workout_id}")
@limiter.limit("10/minute")
async def update_workout_date(workout_id: str, request: Request, user: dict = Depends(verify_token)):
    try:
        body = await request.json()
        new_date = body.get('date') # Expects YYYY-MM-DD
        
        if not new_date:
             raise HTTPException(status_code=400, detail="New date is required")

        if db_manager.update_workout_date(user['uid'], workout_id, new_date):
            return {"status": "success", "message": "Workout rescheduled"}
        else:
             raise HTTPException(status_code=404, detail="Workout not found or permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/workouts/{workout_id}")
@limiter.limit("10/minute")
async def delete_workout_endpoint(workout_id: str, request: Request, user: dict = Depends(verify_token)):
    try:
        # We need a delete function in db_manager or use generic delete if exposed?
        # firestore_manager.delete_goal exists, but not delete_workout explicitly with ID check.
        # But we can use db.collection(...).delete() wrapper.
        # Let's assume we can add it or modify firestore_manager efficiently?
        # Or just do:
        doc_ref = db_manager.db.collection('workouts').document(workout_id)
        doc = doc_ref.get()
        if not doc.exists:
             raise HTTPException(status_code=404, detail="Workout not found")
        if doc.to_dict().get('user_id') != user['uid']:
             raise HTTPException(status_code=403, detail="Permission denied")
        
        doc_ref.delete()
        return {"status": "success", "message": "Workout deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plans/history")
async def get_plan_history(limit: int = 5, user: dict = Depends(verify_token)):
    # Switch to Firestore
    return db_manager.get_recent_plans(user['uid'], limit=limit)

@app.get("/readiness")
@limiter.limit("20/minute")
def get_readiness(request: Request, user: dict = Depends(verify_token)):
    try:
        # Migrated: Use Firestore
        res = db_manager.get_latest_readiness(user['uid'])
        if not res:
            return {"readiness": "--", "date": ""}
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Garmin Credentials Endpoints
# ========================================

class GarminCredentials(BaseModel):
    username: str
    password: str

@app.post("/garmin/credentials")
@limiter.limit("5/hour")
async def save_garmin_credentials_endpoint(
    request: Request,
    credentials: GarminCredentials,
    user: dict = Depends(verify_token)
):
    """
    Saves encrypted Garmin credentials for the authenticated user.
    
    Security:
    - Password is encrypted before storage using AES-256
    - Rate limited to 5 requests per hour
    - Only user can save their own credentials
    """
    try:
        success = db_manager.save_garmin_credentials(
            user['uid'],
            credentials.username,
            credentials.password
        )
        
        if success:
            return {
                "status": "success",
                "message": "Garmin credentials saved securely"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save credentials")
            
    except ValueError as e:
        # Encryption key not configured
        raise HTTPException(status_code=500, detail=f"Server configuration error: {str(e)}")
    except Exception as e:
        print(f"Save Garmin Credentials Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/garmin/status")
@limiter.limit("20/minute")
async def get_garmin_status_endpoint(
    request: Request,
    user: dict = Depends(verify_token)
):
    """
    Checks if user has saved Garmin credentials.
    
    Returns:
        {
            "connected": true/false,
            "username": "user@example.com" (if connected)
        }
    """
    try:
        has_credentials = db_manager.check_garmin_credentials_exist(user['uid'])
        
        if has_credentials:
            # Get username (but NOT password)
            creds = db_manager.get_garmin_credentials(user['uid'])
            return {
                "connected": True,
                "username": creds['username'] if creds else None
            }
        else:
            return {
                "connected": False,
                "username": None
            }
            
    except Exception as e:
        print(f"Garmin Status Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/garmin/credentials")
@limiter.limit("5/hour")
async def delete_garmin_credentials_endpoint(
    request: Request,
    user: dict = Depends(verify_token)
):
    """
    Deletes user's Garmin credentials (disconnect).
    """
    try:
        success = db_manager.delete_garmin_credentials(user['uid'])
        
        if success:
            return {
                "status": "success",
                "message": "Garmin account disconnected"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete credentials")
            
    except Exception as e:
        print(f"Delete Garmin Credentials Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


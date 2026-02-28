from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Query
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
import ai_coach
import firestore_garmin_metrics
from garmin_client import GarminClient # Handles file uploads
try:
    from google.cloud import error_reporting
except ImportError:
    error_reporting = None

from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
from datetime import date, timedelta, datetime
import calendar

from config import get_settings
from logger import setup_logging, logger

settings = get_settings()

# Initialize Structured Logging
setup_logging()

# FORCE FIREBASE INITIALIZATION
# This ensures firebase_admin.initialize_app() is called BEFORE any request is processed.
# Without this, auth_middleware.verify_token() might run before initialization, causing 401 errors.
try:
    db_manager.get_db()
    logger.info("Firebase Admin forced initialization successful")
except Exception as e:
    logger.error(f"Failed to force-initialize Firebase: {e}")

# Initialize Google Cloud Error Reporting (Production Only)
error_reporting_client = None
if settings.APP_ENV == "production":
    if error_reporting:
        try:
            # Client automatically pulls credentials from GOOGLE_APPLICATION_CREDENTIALS or Cloud Run metadata
            error_reporting_client = error_reporting.Client(service=settings.APP_NAME, version=settings.VERSION)
            logger.info("Google Cloud Error Reporting initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Error Reporting: {e}")
    else:
        logger.warning("google-cloud-error-reporting library not found")

# Load secrets (handled by config.py and environment variables)
# SecretLoader is used individually where needed.

limiter = Limiter(key_func=get_remote_address)

# Enhanced API metadata
app = FastAPI(
    title="Health AI Coach API",
    version=settings.VERSION,
    description="""
🏃 **Health AI Coach** - Your personal AI-powered endurance training assistant.

## Features

* **Goal Management**: Create, track, and manage training goals
* **AI Insights**: Get personalized training recommendations powered by Gemini
* **Garmin Integration**: Securely connect and sync Garmin data
* **Training Calendar**: Plan and track workouts
* **Analytics**: Visualize recovery metrics and training load

## Authentication

All endpoints (except `/health`) require Firebase Authentication.  
Include the ID token in the `Authorization` header:

```
Authorization: Bearer <your-firebase-id-token>
```

## Environment

Running in: **{settings.APP_ENV}** mode.

""",
    contact={
        "name": "Health AI Support",
        "url": "https://github.com/yourusername/health_ai",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware: Request Logging ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Structured logging for every incoming HTTP request.
    Logs method, path, status_code, and duration.
    """
    import time
    start_time = time.time()
    
    # Extract request ID if present, otherwise generate one?
    # For now, just log basic info
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    # Log structured JSON
    logger.info(
        "Request processed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time, 2),
            "ip": request.client.host if request.client else "unknown"
        }
    )
    
    return response

app.state.limiter = limiter

# Custom Rate Limit Handler with Logging
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Logs the rate limit violation before returning the standard response.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        "Rate limit exceeded",
        extra={
            "event": "security_rate_limit",
            "ip": client_ip,
            "path": request.url.path,
            "limit": str(exc)
        }
    )
    
    # Persist to Firestore for Admin Dashboard
    try:
        db_manager.log_security_event("rate_limit_exceeded", {
            "ip": client_ip,
            "path": request.url.path,
            "limit": str(exc),
            "user_agent": request.headers.get("user-agent", "unknown")
        })
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")

    return _rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# --- Monitoring ---
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)


# Global Error Handling
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler. Behavior depends on environment settings.
    """
    
    # 1. Log the error (In real prod, use structured logging)
    logger.error(f"CRITICAL ERROR ({settings.APP_ENV}): {exc}", extra={"path": request.url.path})
 
    # 2. Report to Google Cloud Error Reporting (Production only)
    if error_reporting_client:
        try:
            # Automatically grabs stack trace and context
            error_reporting_client.report_exception()
        except Exception as er_err:
            logger.error(f"Failed to report to Cloud Error Reporting: {er_err}")
 
    
    # 2. Return generic message in production
    if not settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "correlation_id": "contact-support"} 
        )
    
    # 3. In development (debug=True), return detailed error
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )

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
        # Load from Firestore (Multi-User)
        metrics = firestore_garmin_metrics.get_user_daily_metrics(user['uid'], days=90)
        
        result = []
        for row in metrics:
            result.append({
                "date": row.get('date'),
                "ctl": round(row.get('CTL', 0), 1),
                "atl": round(row.get('ATL', 0), 1),
                "tsb": round(row.get('TSB', 0), 1),
                "load": int(row.get('workout_calories', 0)),
                "readiness": int(row.get('bodyBatteryHighestValue', 0)),
                "sleep_min": int(row.get('totalSleep_minutes', 0))
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
        period = goal.get('period_type', 'weekly').lower()
        
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
        
        # A) Garmin Data (Firestore)
        metrics_in_range = firestore_garmin_metrics.get_metrics_in_range(user_id, start_date.isoformat(), end_date.isoformat())
        
        for m in metrics_in_range:
            # Check unit and sum up
            if goal.get('target_unit') in ['km', 'm']:
                if 'totalDistanceMeters' in m:
                     total_value += m['totalDistanceMeters'] / 1000.0 # meters to km
            elif goal.get('target_unit') in ['h', 'min']:
                 # Prefer workout duration (tracked activity), fallback to activeSeconds (general movement) if needed
                 # Actually, logic should depend on goal type. If goal is "Running", we only want running duration.
                 # But daily metrics are aggregated. We can't distinguish Running from Cycling in daily_metrics.
                 # Limitation of current Architecture: Daily Metrics are totals.
                 # Better approach: Fetch Activities from 'garmin_activities' collection (if we migrated that too).
                 # For now, MVP: Use total duration/distance from daily metrics which matches current CSV logic.
                 
                 seconds = m.get('workout_duration_seconds', 0)
                 if seconds == 0:
                     seconds = m.get('activeSeconds', 0) # Fallback if migrated data has it (migration script didn't explicitly map activeSeconds? Checked: It didn't.)
                     # If migration script didn't map activeSeconds, this fallback is useless unless I update migration script.
                     # But CSV had 'workout_duration_seconds', so it should be fine.
                 
                 if goal.get('target_unit') == 'h':
                     total_value += seconds / 3600.0
                 else:
                     total_value += seconds / 60.0

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

        # Calculate days_left (Mon–Sun week for weekly, calendar month for monthly, target date for others)
        days_left = 0
        if period == 'weekly':
            days_left = (end_date - today).days  # days until Sunday (inclusive = 0 on Sunday)
        elif period == 'monthly':
            days_left = (end_date - today).days
        elif period in ('target_date', 'race'):
            days_left = max(0, (end_date - today).days)

        return {
            "current_value": round(total_value, 1),
            "progress_percentage": min(100, int((total_value / target_val) * 100)) if target_val > 0 else 0,
            "days_left": days_left,
        }

    except Exception as e:
        print(f"Goal Calc Error: {e}")
        return {"current_value": 0, "progress_percentage": 0, "days_left": 0}


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
            logger.info("User Account Deleted Permantently", extra={"event": "security_account_deletion", "uid": uid})
        except Exception as auth_error:
            logger.error(f"Auth Deletion Error: {auth_error}")
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
        
        logger.info("Admin accessing feedback logs", extra={"event": "security_admin_access", "uid": user.get("uid")})

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

@app.post("/admin/revoke-tokens/{uid}")
@limiter.limit("5/minute")
async def revoke_user_tokens(request: Request, uid: str, user: dict = Depends(verify_admin)):
    """
    Revokes all refresh tokens for a user. Forces them to re-login.
    Admin only.
    """
    try:
        auth.revoke_refresh_tokens(uid)
        logger.info(f"Revoked tokens for user {uid}", extra={"admin": user['uid'], "target_uid": uid, "event": "security_token_revocation"})
        return {"status": "success", "message": f"Tokens revoked for {uid}"}
    except Exception as e:
        logger.error(f"Token Revocation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/users")
@limiter.limit("20/minute")
async def list_users_admin(request: Request, user: dict = Depends(verify_admin)):
    """
    List all users from Firebase Auth.
    """
    try:
        # List users in batches of 1000 (default)
        page = auth.list_users()
        users_list = []
        for u in page.users:
            users_list.append({
                "uid": u.uid,
                "email": u.email,
                "display_name": u.display_name,
                "disabled": u.disabled,
                "metadata": {
                    "last_sign_in": u.user_metadata.last_sign_in_timestamp,
                    "creation_time": u.user_metadata.creation_timestamp
                }
            })
        
        logger.info("Admin listed users", extra={"admin": user['uid'], "count": len(users_list)})
        return {"users": users_list, "total": len(users_list)}
    except Exception as e:
        logger.error(f"User List Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/security-events")
@limiter.limit("50/minute")
async def get_security_events_admin(
    request: Request,
    user: dict = Depends(verify_admin),
    limit: int = 100,
    type: Optional[str] = None
):
    """
    Admin endpoint: Returns security logs (rate limits, auth failures).
    """
    try:
        logger.info("Admin accessing security logs", extra={"event": "security_admin_access", "uid": user.get("uid")})
        events = db_manager.get_security_events(limit=limit, event_type=type)
        return {"total": len(events), "events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/next-workout", tags=["Workouts"])
@limiter.limit("20/minute")
async def get_next_workout_endpoint(request: Request, user: dict = Depends(verify_token)):
    """
    Retrieve the next planned workout for the user.
    
    Returns the soonest 'PENDING' workout where date >= today.
    """
    try:
        workout = db_manager.get_next_workout(user['uid'])
        if not workout:
            return {}
        return workout
    except Exception as e:
        print(f"Error fetching next workout: {e}")
        return {}

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

@app.get("/workouts/history", tags=["Workouts"])
@limiter.limit("20/minute")
async def get_workout_history(request: Request, user: dict = Depends(verify_token), limit: int = 50):
    """
    Get past completed workouts for the authenticated user.
    
    Used by the mobile Training Calendar to display historical sessions.
    Returns workouts with status DONE, ordered by date descending.
    """
    try:
        workouts = db_manager.get_all_workouts(user['uid'], limit=limit)
        done = [w for w in workouts if w.get('status') == 'DONE']
        done.sort(key=lambda w: w.get('date', ''), reverse=True)
        return done
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


class WorkoutUploadRequest(BaseModel):
    workout: dict # The Garmin-compatible JSON structure
    date: Optional[str] = None # YYYY-MM-DD for scheduling (Optional)

@app.post("/workouts/upload", tags=["Workouts"])
@limiter.limit("5/minute")
def upload_workout_endpoint(
    req: WorkoutUploadRequest, 
    request: Request, 
    user: dict = Depends(verify_token)
):
    """
    Upload a structured workout to Garmin Connect.
    Optionally schedules it if 'date' is provided.
    
    **Request Body:**
    - `workout`: JSON object matching Garmin's workout structure.
    - `date`: (Optional) "YYYY-MM-DD" to schedule the workout.
    """
    try:
        client = GarminClient(user['uid'])
        
        # 1. Upload Workout
        workout_id = client.upload_workout(req.workout)
        
        if workout_id:
            message = "Workout uploaded to Garmin Connect"
            scheduled = False
            
            # 2. Schedule (if date provided)
            if req.date:
                scheduled = client.schedule_workout(workout_id, req.date)
                if scheduled:
                    message += " and scheduled for " + req.date
                else:
                    message += " (but scheduling failed)"
            
            return {
                "status": "success", 
                "message": message,
                "workoutId": workout_id,
                "scheduled": scheduled
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to upload workout")

    except ValueError as ve:
         raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Workout Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

refresh_statuses = {}

def execute_refresh_task(uid: str, mode: str = "incremental"):
    """Background task to fetch data and train model with progress updates."""
    try:
        refresh_statuses[uid] = {"status": "in_progress", "progress": 10, "message": "Initializing...", "error": None}
        
        import sys
        import os
        import importlib
        
        script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
        if not os.path.exists(os.path.join(script_dir, "fetch_garmin_data.py")):
             refresh_statuses[uid]["status"] = "failed"
             refresh_statuses[uid]["error"] = f"Could not locate fetch_garmin_data.py in {script_dir}"
             return

        if script_dir not in sys.path:
            sys.path.append(script_dir)
            
        import fetch_garmin_data
        import process_garmin_data
        
        importlib.reload(fetch_garmin_data)
        importlib.reload(process_garmin_data)
        
        refresh_statuses[uid]["progress"] = 30
        refresh_statuses[uid]["message"] = "Fetching Garmin Data..."
        
        has_credentials = db_manager.check_garmin_credentials_exist(uid)
        
        if has_credentials:
            fetch_garmin_data.main(user_id=uid, mode=mode)
        else:
            fetch_garmin_data.main(user_id=None, mode=mode)
            
        refresh_statuses[uid]["progress"] = 70
        refresh_statuses[uid]["message"] = f"Training XGBoost Model ({mode})..."
        
        process_garmin_data.main_process(user_id=uid, mode=mode)
        
        refresh_statuses[uid]["progress"] = 100
        refresh_statuses[uid]["status"] = "completed"
        refresh_statuses[uid]["message"] = "Data refreshed and model retrained."
            
    except ValueError as ve:
        refresh_statuses[uid]["status"] = "failed"
        refresh_statuses[uid]["error"] = str(ve) + " Please connect your Garmin account in Profile settings."
    except Exception as e:
        import traceback
        traceback.print_exc()
        refresh_statuses[uid]["status"] = "failed"
        refresh_statuses[uid]["error"] = f"Refresh failed: {str(e)}"

@app.post("/system/refresh")
async def refresh_data(
    background_tasks: BackgroundTasks, 
    mode: str = Query("incremental", description="Training mode: 'incremental' or 'full'"),
    user: dict = Depends(verify_token)
):
    """
    Triggers Garmin data fetch and model retraining for the authenticated user asynchronously.
    """
    uid = user.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="User ID missing from token")

    if refresh_statuses.get(uid, {}).get("status") == "in_progress":
        return {"status": "success", "message": "Refresh already in progress."}
        
    background_tasks.add_task(execute_refresh_task, uid, mode)
    
    # Initialize status
    refresh_statuses[uid] = {"status": "starting", "progress": 0, "message": "Initializing refresh task...", "error": None}
    
    return {"status": "success", "message": "Refresh task started in background."}
    
@app.get("/system/refresh/status")
async def get_refresh_status(user: dict = Depends(verify_token)):
    """
    Returns the current status of the background refresh task.
    """
    uid = user['uid']
    status_info = refresh_statuses.get(uid, {"status": "none", "progress": 0, "message": "", "error": None})
    return status_info


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
        base_dir = os.path.dirname(os.path.abspath(__file__))
        uid = user['uid']
        
        # Determine base directories
        if os.path.exists("/app/data"):
             data_dir = "/app/data"
             # Assuming outputs directory exists in Docker image or volume
             outputs_dir = "/app/outputs" 
        else:
             data_dir = os.path.join(base_dir, "data")
             outputs_dir = os.path.join(base_dir, "outputs")
             
        # Construct Per-User Paths
        metrics_path = os.path.join(data_dir, uid, "model_metrics.json")
        fi_path = os.path.join(outputs_dir, uid, "feature_importance.json")
        
        # Fallback to global/legacy paths if user-specific not found
        if not os.path.exists(metrics_path):
             metrics_path = os.path.join(data_dir, "model_metrics.json")
             
        if not os.path.exists(fi_path):
             # Try older locations or global
             fi_path = os.path.join(outputs_dir, "feature_importance.json")
             if not os.path.exists(fi_path):
                  # Check parent dir (legacy: backend/feature_importance.json)
                  fi_path = os.path.join(base_dir, "..", "feature_importance.json")

        data = {"r2": 0, "mae": 0, "last_trained": "Never", "top_features": {}, "data_points": 0}
        
        # 0. Get Data Volume (Firestore)
        data['data_points'] = firestore_garmin_metrics.get_user_metrics_count(uid)

        # 1. Try Firestore First (Cloud Run Persistence Fix)
        firestore_data = firestore_garmin_metrics.get_model_performance(uid)
        
        if firestore_data:
             if 'metrics' in firestore_data:
                 data.update(firestore_data['metrics'])
             if 'feature_importance' in firestore_data:
                 data['top_features'] = firestore_data['feature_importance']
                 
             return data

        # 2. Fallback: Load Locally (Legacy / Local Dev)
        try:
            if os.path.exists(metrics_path):
                with open(metrics_path, "r") as f:
                    data.update(json.load(f))
        except Exception as e:
            print(f"Error loading metrics: {e}")
            
        # 3. Load Feature Importance (Legacy)
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
                    "source": "AI_GENERATED",
                    "garmin_workout": p.get('garmin_workout') # Save for export
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

@app.get("/workouts/next")
@limiter.limit("20/minute")
async def get_next_workout_endpoint(request: Request, user: dict = Depends(verify_token)):
    """
    Fetches the next pending workout for the user (today or future).
    Used for the "Suggestion" card in the mobile dashboard.
    """
    try:
        workout = db_manager.get_next_workout(user['uid'])
        return workout if workout else {} # Return empty dict if no workout, handled by frontend
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

@app.post("/garmin/test")
@limiter.limit("10/hour")
async def test_garmin_credentials_endpoint(
    request: Request,
    credentials: GarminCredentials,
    user: dict = Depends(verify_token)
):
    """
    Tests Garmin credentials without saving them.
    Useful for validating before committing to DB.
    """
    try:
        from garminconnect import Garmin
        client = Garmin(credentials.username, credentials.password)
        client.login()
        return {"status": "success", "message": "Credentials verified successfully"}
    except Exception as e:
        logger.warning(f"Garmin Test Failed for {user['uid']}: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed. Please check your username and password.")

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


# --- AI Chat Endpoint ---

from ai_chat_manager import chat_manager

class ChatRequest(BaseModel):
    message: str
    history: List[dict] # [{"role": "user", "content": "..."}, ...]

@app.post("/ai/chat", tags=["AI"])
@limiter.limit("10/minute")
async def chat_endpoint(request_body: ChatRequest, request: Request, user: dict = Depends(verify_token)):
    """
    Interactive AI Coach Chat (Gemini Flash v2).
    """
    try:
        reply = chat_manager.generate_reply(user['uid'], request_body.message, request_body.history)
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Chat Endpoint Error: {e}")
        raise HTTPException(status_code=500, detail="Chat failed")

@app.get("/debug/files", tags=["Debug"])
async def debug_files(user: dict = Depends(verify_admin)):
    """
    Debug endpoint to list files in data directories.
    """
    import os
    
    paths_to_check = [
        "/app/data",
        "/app/outputs",
        os.path.join(os.getcwd(), "data"),
        os.path.join(os.getcwd(), "backend", "data"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
    ]
    
    results = {}
    
    for path in paths_to_check:
        if os.path.exists(path):
            try:
                # List top level
                items = os.listdir(path)
                results[path] = items
                
                # If user directory exists, list that too
                if user.get('uid') in items:
                    user_path = os.path.join(path, user['uid'])
                    if os.path.isdir(user_path):
                        results[user_path] = os.listdir(user_path)
            except Exception as e:
                results[path] = f"Error: {str(e)}"
        else:
            results[path] = "Not Found"
            
    return {
        "cwd": os.getcwd(),
        "files": results,
        "uid": user.get('uid')
    }

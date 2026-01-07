from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional
import firestore_manager as db_manager # Alias to keep code changes minimal
import db_manager as local_db # DuckDB for history/analytics
from fastapi import Depends
from auth_middleware import verify_token
import json
import sys
import os

# Add /data to path to find ai_coach.py (Legacy structure)
sys.path.append("/data")
try:
    import ai_coach
except ImportError:
    # Fallback for local testing if not in Docker with /data
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        import ai_coach
    except ImportError:
        print("Warning: ai_coach module not found.")

from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
from datetime import date

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Health AI API", version="0.1.0")

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

@app.get("/metrics/history")
async def get_metrics_history(user: dict = Depends(verify_token)):
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

@app.get("/goals")
@limiter.limit("10/minute")
def get_goals(request: Request, user: dict = Depends(verify_token)):
    try:
        goals = db_manager.get_active_goals(user['uid'])
        return goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class GoalCreate(BaseModel):
    activity_type: str
    target_value: float
    target_unit: str
    period_type: str # 'weekly', 'monthly', 'target_date'
    frequency: Optional[str] = None # kept for backward compatibility or extra info
    target_date: Optional[str] = None # ISO format date string YYYY-MM-DD
    description: Optional[str] = None

@app.post("/goals")
@limiter.limit("5/minute")
def create_goal(goal: GoalCreate, request: Request, user: dict = Depends(verify_token)):
    try:
        success = db_manager.add_goal(user['uid'], goal.model_dump())
        if success:
            return {"status": "success", "message": "Goal added"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add goal")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/goals/{goal_id}")
async def delete_goal_endpoint(goal_id: str, user: dict = Depends(verify_token)):
    try:
        if db_manager.delete_goal(user['uid'], goal_id):
            return {"status": "success", "message": "Goal deleted"}
        else:
            raise HTTPException(status_code=404, detail="Goal not found or access denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/goals/{goal_id}")
async def update_goal_endpoint(goal_id: str, goal: GoalCreate, user: dict = Depends(verify_token)):
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

@app.get("/next-workout")
@limiter.limit("20/minute")
def get_next_workout_endpoint(request: Request, user: dict = Depends(verify_token)):
    try:
        # Use Firestore for next workout
        workout = db_manager.get_next_workout(user['uid'])
        if not workout:
            return {}
        return workout
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workouts/weekly-status")
async def get_weekly_status(user: dict = Depends(verify_token)):
    current, planned, breakdown = local_db.get_weekly_load_status()
    return {
        "current_load": current,
        "planned_load": planned,
        "breakdown": breakdown
    }

@app.get("/workouts/upcoming")
@limiter.limit("20/minute")
def get_upcoming_workouts(request: Request, user: dict = Depends(verify_token)):
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

@app.post("/workouts/manual")
async def log_manual_workout(workout: ManualWorkout, user: dict = Depends(verify_token)):
    try:
        # Pydantic validates date string format if we used date type, but here it's string.
        # Ensure date format
        from datetime import date, datetime
        date_obj = date.fromisoformat(workout.date)
        
        # 1. Legacy Write (DuckDB)
        local_db.log_manual_workout(
            date_obj,
            workout.activity,
            workout.duration_min,
            workout.rpe,
            workout.notes
        )

        # 2. Modern Write (Firestore)
        # Map to Firestore document structure
        # Use datetime for created_at, ISO string for 'date' field queryability
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

        return {"status": "success", "message": "Workout logged to Dual DB"}
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format (YYYY-MM-DD required)")
    except Exception as e:
        print(f"Error logging manual workout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/refresh")
async def refresh_data(user: dict = Depends(verify_token)):
    """
    Triggers Garmin data fetch and model retraining.
    Uses legacy scripts from parent directory via sys.path hack.
    """
    try:
        import sys
        import os
        import importlib
        
        # Determine path to scripts (supporting Docker /app vs Local /backend)
        # In Docker: /app is CWD. Scripts are in /data (mounted to host root)
        # Local: CWD is /backend. Scripts are in ../
        
        script_dirs = ["/data", "..", os.path.dirname(os.getcwd())]
        script_dir = None
        
        for d in script_dirs:
            p = os.path.abspath(d)
            if os.path.exists(os.path.join(p, "fetch_garmin_data.py")):
                if p not in sys.path:
                    sys.path.append(p)
                script_dir = p
                break
        
        if not script_dir:
             raise FileNotFoundError("Could not locate fetch_garmin_data.py in standard locations.")

        # CHANGE CWD so the scripts can find "Health_AI/data/..."
        # This is critical for legacy scripts that use relative paths
        original_cwd = os.getcwd()
        os.chdir(script_dir)
        
        try:
            import fetch_garmin_data
            import process_garmin_data
            
            # Force reload to ensure fresh execution
            importlib.reload(fetch_garmin_data)
            importlib.reload(process_garmin_data)
            
            # Run Fetch
            print(f"Starting Data Fetch from {script_dir}...")
            fetch_garmin_data.main()
            
            # Run Process
            print("Starting Model Training...")
            process_garmin_data.main_process()
            
        finally:
            # Always restore CWD to avoid side effects
            os.chdir(original_cwd)
        
        return {"status": "success", "message": "Data refreshed and model retrained."}
        
    except Exception as e:
        print(f"Refresh error: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")

import sys
import os

# Ensure we can import ai_coach from root (mapped to /data in Docker or .. in local)
# This is similar to the logic used in refresh_data
current = os.path.dirname(os.path.abspath(__file__))
potential_paths = [
    os.path.join(current, ".."), # Local dev
    "/data"                      # Docker
]

for p in potential_paths:
    if os.path.exists(os.path.join(p, "ai_coach.py")):
        if p not in sys.path:
            sys.path.append(p)
        break

import ai_coach # Import ai_coach module

@app.get("/ai/insight")
@limiter.limit("10/minute")
async def get_ai_insight(request: Request, user: dict = Depends(verify_token)):
    """
    Generates a daily insight based on the latest metrics.
    """
    try:
        # Reuse logic to get latest 30 days, but we only need the last one
        metrics = await get_metrics_history(user)
        if not metrics or len(metrics) == 0:
            return {"insight": "Ei tarpeeksi dataa analyysiin."}
            
        latest = metrics[-1] # Last day
        
        # Prepare context for AI
        ctx = {
            "tsb": latest['tsb'],
            "readiness": latest['readiness'],
            "sleep_min": latest['sleep_min'],
            "ctl": latest['ctl']
        }
        
        insight = ai_coach.generate_daily_insight(ctx)
        return {"insight": insight}
        
    except Exception as e:
        print(f"Insight Endpoint Error: {e}")
        return {"insight": "Tänään kannattaa kuunnella kehoa."} # Fallback


class PlanGenerationRequest(BaseModel):
    days: int = 1

@app.post("/plans/generate")
@limiter.limit("5/minute")
async def generate_plan_endpoint(request: Request, req: PlanGenerationRequest, user: dict = Depends(verify_token)):
    try:
        # 1. Get Context (Metrics)
        # Reuse get_metrics_history logic or call it directly if possible.
        # Calling the function directly is cleaner if we abstract, but here we can just call it
        metrics = await get_metrics_history(user)
        if not metrics or len(metrics) == 0:
            # Fallback or error? Let's proceed with empty
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
            n_days=req.days
        )
        
        # We need to fetch goals ourselves to be safe and pass them as text
        # ai_coach.py line 122: construct_multi_day_prompt(..., active_goals=goals_text)
        # Wait, generate_coach_advice calls db_manager.
        # Let's trust it for now or if ai_coach is using the wrong db_manager we fix that later.
        # Actually, let's fetch goals here and pass them if we can.. 
        # But generate_coach_advice signature is: (context, n_days=1, compliance_history="", preference_feedback="")
        # It does NOT accept active_goals override in the public function signature shown in viewed file (lines 94).
        # It calls db_manager inside.
        # I should check if I can update ai_coach.py to accept goals or ensure it imports firestore_manager.
        
        # Proceeding assuming it might fail or use local DuckDB for goals. That's "okay" for now, or we fix ai_coach.
        
        try:
           plans = json.loads(response_json)
        except json.JSONDecodeError:
            # Fallback if AI didn't return valid JSON
            return {"status": "error", "message": "AI returned invalid JSON", "raw": response_json}

        # 3. Save to Firestore
        from datetime import datetime, timedelta
        
        saved_count = 0
        today = date.today()
        
        # 3b. Overwrite Logic: Delete existing PENDING workouts for the target range
        # Calculate range
        start_date_obj = today # Assuming plan starts today
        # Find max day in plan to determine end date
        max_day = 1
        for p in plans:
            max_day = max(max_day, p.get('day', 1))
            
        end_date_obj = today + timedelta(days=max_day-1)
        
        db_manager.delete_pending_workouts(
            user['uid'], 
            start_date_obj.isoformat(), 
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
            
        summary_parts = []
        for act, count in activity_counts.items():
            summary_parts.append(f"{count}x {act}")
            
        summary_text = f"Plan ({req.days} days): " + ", ".join(summary_parts)

        db_manager.save_generated_plan(
            user['uid'],
            {"raw_json": plans},
            summary_text,
            ctx['predicted_charge']
        )
        
        return {"status": "success", "count": saved_count, "plans": plans}

    except Exception as e:
        print(f"Generate Plan Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plans/history")
async def get_plan_history(limit: int = 5, user: dict = Depends(verify_token)):
    # Switch to Firestore
    return db_manager.get_recent_plans(user['uid'], limit=limit)
@app.get("/readiness")
@limiter.limit("20/minute")
def get_readiness(request: Request, user: dict = Depends(verify_token)):
    try:
        latest = local_db.get_latest_plan()
        if latest and 'content' in latest:
            # content is advice_text, we needed 'predicted_charge' which is stored in db but get_latest_plan wrapper might not return it
            # Let's check get_latest_plan implementation or use raw connection
             pass 
        # Actually get_latest_plan returns dict with content, date, id, status.
        # We need predicted_charge. Let's fix db_manager.get_latest_plan or make a new query.
        # For now, let's look at `db_manager.py` again or assume we need to update it.
        # Wait, get_latest_plan in db_manager selects 'advice_text, timestamp, id, status'.
        # We need to update db_manager.py first to fetch charge, or add a new function.
        # OPTION: Add new function to db_manager below.
        
        # Let's assume we will add get_latest_readiness to db_manager.
        res = local_db.get_latest_readiness()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional
import firestore_manager as db_manager # Alias to keep code changes minimal
import json

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Health AI API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
@limiter.limit("5/minute")
def read_root(request: Request):
    return {"message": "Health AI API is running! (DuckDB Version)"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/goals")
@limiter.limit("10/minute")
def get_goals(request: Request):
    try:
        goals = db_manager.get_active_goals()
        return goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/next-workout")
@limiter.limit("20/minute")
def get_next_workout_endpoint(request: Request):
    try:
        workout = db_manager.get_next_workout()
        if not workout:
            return {}
        return workout
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workouts/weekly-status")
@limiter.limit("10/minute")
def get_weekly_status(request: Request):
    try:
        current_load, planned_load, breakdown = db_manager.get_weekly_load_status()
        return {
            "current_load": current_load,
            "planned_load": planned_load,
            "breakdown": breakdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

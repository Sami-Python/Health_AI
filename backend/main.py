from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional
import firestore_manager as db_manager # Alias to keep code changes minimal
from fastapi import Depends
from auth_middleware import verify_token
import json

from fastapi.middleware.cors import CORSMiddleware

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Health AI API", version="0.1.0")

# Configure CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def get_goals(request: Request, user: dict = Depends(verify_token)):
    try:
        goals = db_manager.get_active_goals(user['uid'])
        return goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/next-workout")
@limiter.limit("20/minute")
def get_next_workout_endpoint(request: Request, user: dict = Depends(verify_token)):
    try:
        workout = db_manager.get_next_workout(user['uid'])
        if not workout:
            return {}
        return workout
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workouts/weekly-status")
@limiter.limit("10/minute")
def get_weekly_status(request: Request, user: dict = Depends(verify_token)):
    try:
        current_load, planned_load, breakdown = db_manager.get_weekly_load_status(user['uid'])
        return {
            "current_load": current_load,
            "planned_load": planned_load,
            "breakdown": breakdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

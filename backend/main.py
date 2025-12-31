from fastapi import FastAPI, HTTPException
from typing import List, Optional
import db_manager
import json

app = FastAPI(title="Health AI API", version="0.1.0")

@app.get("/")
def read_root():
    return {"message": "Health AI API is running! (DuckDB Version)"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/goals")
def get_goals():
    try:
        goals = db_manager.get_active_goals()
        return goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/next-workout")
def get_next_workout_endpoint():
    try:
        workout = db_manager.get_next_workout()
        if not workout:
            return {}
        return workout
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workouts/weekly-status")
def get_weekly_status():
    try:
        current_load, planned_load, breakdown = db_manager.get_weekly_load_status()
        return {
            "current_load": current_load,
            "planned_load": planned_load,
            "breakdown": breakdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

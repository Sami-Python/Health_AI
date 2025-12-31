import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

def get_next_workout():
    """Fetches next workout from API."""
    try:
        response = requests.get(f"{API_URL}/next-workout")
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

def get_weekly_status():
    """Fetches weekly load status from API."""
    try:
        response = requests.get(f"{API_URL}/workouts/weekly-status")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_active_goals():
    """Fetches active goals from API."""
    try:
        response = requests.get(f"{API_URL}/goals")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

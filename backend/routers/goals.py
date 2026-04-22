from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import Optional
from datetime import date, timedelta, datetime

from auth_middleware import verify_token
import firestore_manager as db_manager
import firestore_garmin_metrics
from logger import logger

router = APIRouter(prefix="", tags=["Goals"])

limiter = Limiter(key_func=get_remote_address)


class GoalCreate(BaseModel):
    activity_type: str
    target_value: float
    target_unit: str
    period_type: str  # 'weekly', 'monthly', 'target_date'
    frequency: Optional[str] = None  # kept for backward compatibility or extra info
    target_date: Optional[str] = None  # ISO format date string YYYY-MM-DD
    description: Optional[str] = None


def calculate_goal_progress(user_id: str, goal: dict):
    """
    Calculates current progress for a goal based on:
    1. Garmin Data (Firestore)
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
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
        elif period == 'target_date' or period == 'race':
            # Range: From Creation (or fallback) to Target Date
            target_date_str = goal.get('target_date')
            if target_date_str:
                end_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            else:
                end_date = today + timedelta(days=30)  # Fallback

            # Start from creation or if missing, assume reasonable fallback
            created_at = goal.get('created_at')
            if created_at:
                if isinstance(created_at, datetime):
                    start_date = created_at.date()
                elif isinstance(created_at, str):
                    try:
                        start_date = datetime.fromisoformat(created_at).date()
                    except Exception:
                        start_date = datetime(2025, 1, 1).date()
                else:
                    try:
                        start_date = created_at.date()
                    except Exception:
                        start_date = datetime(2025, 1, 1).date()
            else:
                start_date = datetime(2025, 1, 1).date()

        if period == 'race':
            # Race Mode: Calculate countdown
            if not end_date:
                return {"days_remaining": 0, "current_value": 0, "progress_percentage": 0}

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
        metrics_in_range = firestore_garmin_metrics.get_metrics_in_range(
            user_id, start_date.isoformat(), end_date.isoformat()
        )

        for m in metrics_in_range:
            if goal.get('target_unit') in ['km', 'm']:
                if 'totalDistanceMeters' in m:
                    total_value += m['totalDistanceMeters'] / 1000.0
            elif goal.get('target_unit') in ['h', 'min']:
                seconds = m.get('workout_duration_seconds', 0)
                if seconds == 0:
                    seconds = m.get('activeSeconds', 0)

                if goal.get('target_unit') == 'h':
                    total_value += seconds / 3600.0
                else:
                    total_value += seconds / 60.0

        # B) Manual Workouts (Firestore)
        manual_workouts = db_manager.get_workouts_in_range(
            user_id, start_date.isoformat(), end_date.isoformat()
        )
        for w in manual_workouts:
            w_activity = w.get('activity', '').lower()
            if activity_type in w_activity or w_activity in activity_type:
                if goal.get('target_unit') in ['min', 'h']:
                    duration = w.get('duration_min', 0)
                    if goal.get('target_unit') == 'h':
                        total_value += duration / 60.0
                    else:
                        total_value += duration
                elif goal.get('target_unit') in ['km']:
                    pass  # Manual workouts don't store distance currently

        # Calculate days_left
        days_left = 0
        if period == 'weekly':
            days_left = (end_date - today).days
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
        logger.error(f"Goal Calc Error: {e}")
        return {"current_value": 0, "progress_percentage": 0, "days_left": 0}


@router.get("/goals")
@limiter.limit("10/minute")
def get_goals(request: Request, user: dict = Depends(verify_token)):
    """
    Get all active goals for the authenticated user.

    Returns a list of goals with calculated progress based on:
    - Garmin activity data
    - Manual workout logs (Firestore)

    **Goal Types:**
    - `weekly`: Recurring weekly goals (e.g., 50km/week)
    - `monthly`: Recurring monthly goals
    - `target_date`: One-time goals with deadline
    - `race`: Race preparation goals

    **Rate Limit:** 10 requests/minute
    """
    try:
        raw_goals = db_manager.get_active_goals(user['uid'])

        enriched_goals = []
        for g in raw_goals:
            progress = calculate_goal_progress(user['uid'], g)
            g.update(progress)
            enriched_goals.append(g)

        return enriched_goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/goals")
@limiter.limit("5/minute")
def create_goal(goal: GoalCreate, request: Request, user: dict = Depends(verify_token)):
    """
    Create a new training goal.

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


@router.delete("/goals/{goal_id}")
async def delete_goal_endpoint(goal_id: str, user: dict = Depends(verify_token)):
    """
    Delete a specific goal.

    **Note:** Only the goal owner can delete their own goals (enforced by user_id check).
    """
    try:
        if db_manager.delete_goal(user['uid'], goal_id):
            return {"status": "success", "message": "Goal deleted"}
        else:
            raise HTTPException(status_code=404, detail="Goal not found or access denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/goals/{goal_id}")
async def update_goal_endpoint(goal_id: str, goal: GoalCreate, user: dict = Depends(verify_token)):
    """
    Update an existing goal.
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

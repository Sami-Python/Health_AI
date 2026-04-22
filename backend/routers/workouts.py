from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

from auth_middleware import verify_token
import firestore_manager as db_manager
from logger import logger
import ai_coach
from notification_service import notification_service
import firestore_garmin_metrics

router = APIRouter(prefix="", tags=["Workouts"])

limiter = Limiter(key_func=get_remote_address)


class ManualWorkout(BaseModel):
    date: str
    activity: str
    duration_min: int
    rpe: int
    notes: Optional[str] = ""


class WorkoutUploadRequest(BaseModel):
    workout: dict  # The Garmin-compatible JSON structure
    date: Optional[str] = None  # YYYY-MM-DD for scheduling (Optional)


def _process_workout_rescheduling(user_id: str, workout: dict):
    """
    Handles the AI-driven rescheduling logic for a specific workout.
    """
    try:
        # 1. Get current metrics for AI context
        recent_metrics = firestore_garmin_metrics.get_user_daily_metrics(user_id, days=1)
        if not recent_metrics:
            current_metrics = {"date": date.today().isoformat(), "readiness": 50, "tsb": 0}
        else:
            m = recent_metrics[0]
            current_metrics = {
                "date": m.get('date'),
                "readiness": int(m.get('bodyBatteryHighestValue', 50)),
                "tsb": round(m.get('TSB', 0), 1)
            }

        # 2. Generate AI suggestion
        suggestion = ai_coach.generate_rescheduling_suggestion(user_id, workout, current_metrics)
        if not suggestion:
            return None

        # 3. Mark workout as SKIPPED
        db_manager.db.collection('users').document(user_id).collection('workouts') \
            .document(workout['id']).update({'status': 'SKIPPED'})

        # 4. Create the new suggested workout
        new_workout = workout.copy()
        new_workout.pop('id', None)
        new_workout['date'] = suggestion['new_date']
        new_workout['status'] = 'PENDING'
        new_workout['rescheduled_from'] = workout['date']
        new_workout['ai_note'] = suggestion['reasoning']

        db_manager.save_workout(user_id, new_workout)

        # 5. Send Push Notification
        notification_service.send_push_notification(
            user_id,
            title="Treeni rästissä? 🏃",
            body=suggestion['push_message'],
            data={
                "type": "reschedule_suggestion",
                "original_date": workout['date'],
                "new_date": suggestion['new_date']
            }
        )
        logger.info(f"Rescheduled workout for {user_id} from {workout['date']} to {suggestion['new_date']}")
        return suggestion

    except Exception as e:
        logger.error(f"Error in workout rescheduling logic: {e}")
        return None


def check_and_reschedule_missed_workout(user_id: str):
    """
    Internal logic to detect the last missed workout and suggest a reschedule.
    """
    missed = db_manager.get_last_missed_workout(user_id)
    if missed:
        _process_workout_rescheduling(user_id, missed)


@router.get("/next-workout")
@limiter.limit("20/minute")
async def get_next_workout_endpoint_legacy(request: Request, user: dict = Depends(verify_token)):
    """
    Retrieve the next planned workout for the user (legacy endpoint).
    """
    try:
        workout = db_manager.get_next_workout(user['uid'])
        if not workout:
            return {}
        return workout
    except Exception as e:
        logger.error(f"Error fetching next workout: {e}")
        return {}


@router.get("/workouts/next")
@limiter.limit("20/minute")
async def get_next_workout_endpoint(request: Request, user: dict = Depends(verify_token)):
    """
    Fetches the next pending workout for the user (today or future).
    Used for the "Suggestion" card in the mobile dashboard.
    """
    try:
        workout = db_manager.get_next_workout(user['uid'])
        return workout if workout else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workouts/weekly-status", tags=["Analytics"])
async def get_weekly_status(user: dict = Depends(verify_token)):
    """
    Get the summary of training load for the current week.

    Calculates:
    - `current_load`: Sum of load from completed (DONE) workouts
    - `planned_load`: Sum of load from pending (PENDING) workouts
    - `breakdown`: Daily breakdown of the weekly load
    """
    current, planned, breakdown, duration_min = db_manager.get_weekly_load_status(user['uid'])
    return {
        "current_load": current,
        "planned_load": planned,
        "breakdown": breakdown,
        "duration_min": duration_min
    }


@router.get("/workouts/upcoming")
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


@router.get("/workouts/history")
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


@router.post("/workouts/manual")
async def log_manual_workout(workout: ManualWorkout, user: dict = Depends(verify_token)):
    """
    Log a workout manually (e.g., gym session or sport not tracked by Garmin).
    """
    try:
        date_obj = date.fromisoformat(workout.date)

        workout_doc = {
            "date": workout.date,
            "activity": workout.activity,
            "duration_min": workout.duration_min,
            "rpe": workout.rpe,
            "description": workout.notes,
            "status": "DONE",
            "source": "MANUAL",
            "load_estimate": workout.duration_min * workout.rpe,
            "structure": "Manual Log"
        }
        db_manager.save_workout(user['uid'], workout_doc)

        return {"status": "success", "message": "Workout logged successfully"}
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format (YYYY-MM-DD required)")
    except Exception as e:
        logger.error(f"Error logging manual workout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workouts/upload")
@limiter.limit("5/minute")
def upload_workout_endpoint(
    req: WorkoutUploadRequest,
    request: Request,
    user: dict = Depends(verify_token)
):
    """
    Upload a structured workout to Garmin Connect.
    Optionally schedules it if 'date' is provided.
    """
    try:
        from garmin_client import GarminClient
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


@router.post("/workouts/{workout_id}/skip")
async def skip_workout_endpoint(workout_id: str, user: dict = Depends(verify_token)):
    """
    Explicitly skip a workout and trigger AI rescheduling.
    """
    try:
        uid = user['uid']
        workout_ref = db_manager.db.collection('users').document(uid).collection('workouts').document(workout_id)
        workout_doc = workout_ref.get()

        if not workout_doc.exists:
            raise HTTPException(status_code=404, detail="Workout not found")

        workout = workout_doc.to_dict()
        workout['id'] = workout_id

        suggestion = _process_workout_rescheduling(uid, workout)

        if not suggestion:
            return {"status": "skipped", "message": "Workout skipped, but AI could not generate a rescheduling suggestion at this time."}

        return {
            "status": "success",
            "message": "Workout skipped and rescheduled",
            "suggestion": suggestion
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error skipping workout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/workouts/{workout_id}")
@limiter.limit("10/minute")
async def update_workout_date(workout_id: str, request: Request, user: dict = Depends(verify_token)):
    """Update the date of a workout (drag & drop reschedule)."""
    try:
        body = await request.json()
        new_date = body.get('date')

        if not new_date:
            raise HTTPException(status_code=400, detail="New date is required")

        if db_manager.update_workout_date(user['uid'], workout_id, new_date):
            return {"status": "success", "message": "Workout rescheduled"}
        else:
            raise HTTPException(status_code=404, detail="Workout not found or permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workouts/{workout_id}")
@limiter.limit("10/minute")
async def delete_workout_endpoint(workout_id: str, request: Request, user: dict = Depends(verify_token)):
    """Delete a specific workout."""
    try:
        success = db_manager.delete_workout(user['uid'], workout_id)
        if not success:
            raise HTTPException(status_code=404, detail="Workout not found or error deleting")

        return {"status": "success", "message": "Workout deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

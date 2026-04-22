from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Query, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
import threading
import os
import sys

from auth_middleware import verify_token
import firestore_manager as db_manager
import firestore_garmin_metrics
import scripts.predict_readiness as predictor
from notification_service import notification_service
import ai_coach
from logger import logger
from routers.garmin import check_garmin_cooldown, set_garmin_cooldown

router = APIRouter(prefix="", tags=["System"])

limiter = Limiter(key_func=get_remote_address)

# In-memory refresh status store
# NOTE: This is per-instance and won't work across multiple Cloud Run instances.
# For production scale, migrate to Firestore-based status tracking.
refresh_statuses = {}

# In-memory store for active background tasks
_active_refresh_tasks: set = set()
_refresh_lock = threading.Lock()


def handle_garmin_mfa_required(uid: str):
    """Centralized handler for when Garmin demands 2FA/MFA."""
    try:
        logger.warning(f"🔐 Handling Garmin 2FA requirement for uid={uid}")

        db_manager.db.collection('users').document(uid).set({
            "garmin_mfa_required": True,
            "last_sync_error": "MFA Required",
            "last_sync_error_time": datetime.now()
        }, merge=True)

        notification_service.send_push_notification(
            uid,
            "Garmin-yhteys vaatii huomiota",
            "Garmin-istuntosi on vanhentunut. Ole hyvä ja kirjaudu uudelleen sovelluksen asetuksissa jatkaaksesi synkronointia.",
            {"type": "garmin_mfa_required"}
        )
        return True
    except Exception as e:
        logger.error(f"Failed to handle Garmin MFA requirement for {uid}: {e}")
        return False


def execute_refresh_task(uid: str, mode: str = "incremental"):
    """Background task to fetch data and train model with progress updates."""
    try:
        refresh_statuses[uid] = {"status": "in_progress", "progress": 10, "message": "Initializing...", "error": None}

        import importlib

        script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
        if not os.path.exists(os.path.join(script_dir, "fetch_garmin_data.py")):
            # Fallback: scripts dir is inside backend/
            script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
            if not os.path.exists(os.path.join(script_dir, "fetch_garmin_data.py")):
                refresh_statuses[uid]["status"] = "failed"
                refresh_statuses[uid]["error"] = f"Could not locate fetch_garmin_data.py"
                return

        if script_dir not in sys.path:
            sys.path.append(script_dir)

        import fetch_garmin_data
        import process_garmin_data

        refresh_statuses[uid]["progress"] = 30
        refresh_statuses[uid]["message"] = "Fetching Garmin Data..."

        has_credentials = db_manager.check_garmin_credentials_exist(uid)

        remaining = check_garmin_cooldown(uid)
        if remaining:
            wait_min = int(remaining / 60) + 1
            logger.warning(f"🛑 Background sync blocked for {uid}: Active 429 cooldown ({wait_min}m remaining).")
            refresh_statuses[uid]["status"] = "failed"
            refresh_statuses[uid]["error"] = f"Garmin rate-limit is active. Please wait {wait_min} mins before retrying."
            return

        try:
            if mode == "full":
                fetch_garmin_data.main(user_id=uid, mode="full", allow_fresh=False)
            else:
                fetch_garmin_data.main(user_id=uid, mode=mode, allow_fresh=False)
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg:
                logger.warning(f"🛑 Background sync hit Garmin 429 for {uid}. Applying 60-min throttle.")
                set_garmin_cooldown(uid, 3600)

                refresh_statuses[uid]["status"] = "failed"
                refresh_statuses[uid]["error"] = f"Garmin on asettanut rajoituksen (429). Odota 30-60 min. Virhe: {err_msg}"
            elif "session expired" in err_msg.lower() or "re-login" in err_msg.lower() or "re-connect" in err_msg.lower():
                logger.info(f"🔑 Background sync stopped: Session expired for {uid}")
                refresh_statuses[uid]["status"] = "failed"
                refresh_statuses[uid]["error"] = "Garmin-yhteys on vanhentunut. Ole hyvä ja kirjaudu uudelleen profiiliasetuksissa."
            else:
                refresh_statuses[uid]["status"] = "failed"
                refresh_statuses[uid]["error"] = f"Sync failed: {err_msg}"
            raise

        refresh_statuses[uid]["progress"] = 70
        refresh_statuses[uid]["message"] = f"Training XGBoost Model ({mode})..."

        process_garmin_data.main_process(user_id=uid, mode=mode)

        # Update last_sync_time in Firestore
        try:
            now = datetime.now()
            db = db_manager.get_db()
            db.collection('users').document(uid).set({"last_sync_time": now}, merge=True)
            db.collection('users').document(uid).collection('profile').document('metrics').set({"last_sync_time": now}, merge=True)
            logger.info(f"Updated last_sync_time for {uid}")
        except Exception as sync_time_err:
            logger.warning(f"Failed to update last_sync_time: {sync_time_err}")

        # Trigger a fresh readiness prediction
        try:
            pred = predictor.predict_tomorrow_readiness(uid)
            if pred is not None:
                db_manager.save_generated_plan(
                    user_id=uid,
                    plan_data={"type": "sync_update", "source": "garmin_sync"},
                    advice_text="Data synkronoitu onnistuneesti. Valmiustilasi huomiselle on päivitetty.",
                    predicted_charge=int(pred)
                )
                logger.info(f"Refreshed readiness prediction for {uid}: {pred}")
        except Exception as pred_err:
            logger.warning(f"Failed to generate post-sync prediction: {pred_err}")

        refresh_statuses[uid]["progress"] = 100
        refresh_statuses[uid]["status"] = "completed"
        refresh_statuses[uid]["message"] = "Data refreshed, model trained and readiness updated."

        # Check for missed workouts after successful sync/refresh
        try:
            from routers.workouts import check_and_reschedule_missed_workout
            check_and_reschedule_missed_workout(uid)
        except Exception as resch_err:
            logger.error(f"Non-critical error in rescheduling check: {resch_err}")

    except ValueError as ve:
        error_msg = str(ve)
        is_mfa = "GarminMFARequiredError" in error_msg or "Garmin 2FA" in error_msg

        refresh_statuses[uid]["status"] = "failed"

        if is_mfa:
            refresh_statuses[uid]["error"] = "Garmin 2FA vaaditaan. Ole hyvä ja kirjaudu uudelleen profiiliasetuksissa."
            handle_garmin_mfa_required(uid)
        else:
            refresh_statuses[uid]["error"] = error_msg + " Please connect your Garmin account in Profile settings."
    except Exception as e:
        import traceback
        logger.error(f"Refresh task error for {uid}: {traceback.format_exc()}")

        error_msg = str(e)
        is_mfa = "GarminMFARequiredError" in error_msg or "Garmin 2FA" in error_msg

        refresh_statuses[uid]["status"] = "failed"

        if is_mfa:
            refresh_statuses[uid]["error"] = "Garmin 2FA vaaditaan. Ole hyvä ja kirjaudu uudelleen profiiliasetuksissa."
            handle_garmin_mfa_required(uid)
        else:
            refresh_statuses[uid]["error"] = f"Refresh failed: {error_msg}"
    finally:
        with _refresh_lock:
            _active_refresh_tasks.discard(uid)


@router.post("/system/refresh")
async def refresh_data(
    background_tasks: BackgroundTasks,
    mode: str = Query("incremental", description="Training mode: 'incremental' or 'full'"),
    user: dict = Depends(verify_token)
):
    """Triggers Garmin data fetch and model retraining asynchronously."""
    uid = user.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="User ID missing from token")

    with _refresh_lock:
        if uid in _active_refresh_tasks:
            return {"status": "already_syncing", "message": "A data sync is already in progress."}
        _active_refresh_tasks.add(uid)

    logger.info(f"🔄 Triggering background refresh for user {uid} (mode={mode})")
    background_tasks.add_task(execute_refresh_task, uid, mode)

    refresh_statuses[uid] = {"status": "starting", "progress": 0, "message": "Initializing refresh task...", "error": None}

    return {"status": "success", "message": "Refresh task started in background."}


@router.get("/system/refresh/status")
async def get_refresh_status(user: dict = Depends(verify_token)):
    """Returns the current status of the background refresh task."""
    uid = user['uid']
    status_info = refresh_statuses.get(uid, {"status": "none", "progress": 0, "message": "", "error": None})
    return status_info


@router.post("/system/auto-sync/enable")
async def enable_auto_sync(request: Request, user: dict = Depends(verify_token)):
    """Toggle auto-sync for the user."""
    uid = user['uid']
    try:
        data = await request.json()
        enabled = data.get('enabled', False)
        db_manager.get_db().collection('users').document(uid).set({'auto_sync_enabled': enabled}, merge=True)
        return {"status": "ok", "auto_sync_enabled": enabled}
    except Exception as e:
        logger.error(f"Auto-sync toggle error for uid={uid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/auto-sync/status")
async def get_auto_sync_status(user: dict = Depends(verify_token)):
    """Check if auto-sync is enabled for the user."""
    uid = user['uid']
    try:
        doc = db_manager.get_db().collection('users').document(uid).get()
        if doc.exists:
            return {"auto_sync_enabled": doc.to_dict().get('auto_sync_enabled', False)}
        return {"auto_sync_enabled": False}
    except Exception as e:
        return {"auto_sync_enabled": False}

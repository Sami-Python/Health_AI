from fastapi import APIRouter, HTTPException, Request, Depends
from firebase_admin import auth
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import Optional

from auth_middleware import verify_token, verify_admin
import firestore_manager as db_manager
import firestore_garmin_metrics
import ai_coach
from notification_service import notification_service
from logger import logger

router = APIRouter(prefix="", tags=["Admin"])

limiter = Limiter(key_func=get_remote_address)


@router.get("/admin/feedback")
@limiter.limit("20/minute")
async def get_all_feedback_admin(
    request: Request,
    user: dict = Depends(verify_admin),
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100
):
    """Admin endpoint: Returns all user feedback."""
    try:
        logger.info("Admin accessing feedback logs", extra={"event": "security_admin_access", "uid": user.get("uid")})
        all_feedback = db_manager.get_all_feedback(limit=limit)

        filtered = all_feedback
        if status:
            filtered = [f for f in filtered if f.get('status') == status]
        if category:
            filtered = [f for f in filtered if f.get('category') == category]

        return {"total": len(filtered), "feedback": filtered}
    except Exception as e:
        logger.error(f"Admin Feedback Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/revoke-tokens/{uid}")
@limiter.limit("5/minute")
async def revoke_user_tokens(request: Request, uid: str, user: dict = Depends(verify_admin)):
    """Revokes all refresh tokens for a user. Forces them to re-login. Admin only."""
    try:
        auth.revoke_refresh_tokens(uid)
        logger.info(f"Revoked tokens for user {uid}", extra={"admin": user['uid'], "target_uid": uid, "event": "security_token_revocation"})
        return {"status": "success", "message": f"Tokens revoked for {uid}"}
    except Exception as e:
        logger.error(f"Token Revocation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/users")
@limiter.limit("20/minute")
async def list_users_admin(request: Request, user: dict = Depends(verify_admin)):
    """List all users from Firebase Auth."""
    try:
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


@router.get("/admin/security-events")
@limiter.limit("50/minute")
async def get_security_events_admin(
    request: Request,
    user: dict = Depends(verify_admin),
    limit: int = 100,
    type: Optional[str] = None
):
    """Admin endpoint: Returns security logs (rate limits, auth failures)."""
    try:
        logger.info("Admin accessing security logs", extra={"event": "security_admin_access", "uid": user.get("uid")})
        events = db_manager.get_security_events(limit=limit, event_type=type)
        return {"total": len(events), "events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/trigger-morning-briefings")
async def admin_trigger_morning_briefings(user: dict = Depends(verify_admin)):
    """
    Admin-only: Trigger morning briefings for ALL users with Garmin connected.
    Intended to be called via Google Cloud Scheduler every morning at 07:00.
    """
    try:
        import threading

        users_docs = db_manager.get_db().collection('users').limit(100).stream()

        results = {"sent": 0, "skipped": 0, "errors": 0}

        def process_user(uid: str):
            try:
                creds = db_manager.get_garmin_credentials(uid)
                if not creds:
                    results['skipped'] += 1
                    return

                latest_metric = firestore_garmin_metrics.get_latest_metric(uid)
                ctx = {}
                if latest_metric:
                    ctx = {
                        'readiness': int(latest_metric.get('bodyBatteryHighestValue', 0)),
                        'tsb': round(float(latest_metric.get('TSB', 0) or 0), 1),
                        'sleep_min': int(latest_metric.get('totalSleep_minutes', 0)),
                        'ctl': round(float(latest_metric.get('CTL', 0) or 0), 1),
                    }

                next_wk = db_manager.get_next_workout(uid)
                if next_wk:
                    ctx['next_workout'] = next_wk.get('content', {}).get('activity', '')

                briefing = ai_coach.generate_morning_briefing(ctx)
                sent = notification_service.send_push_notification(
                    uid,
                    title=briefing['title'],
                    body=briefing['body'],
                    data={'type': 'morning_briefing'}
                )
                if sent:
                    results['sent'] += 1
                else:
                    results['skipped'] += 1

            except Exception as ue:
                logger.warning(f"Morning briefing failed for uid={uid}: {ue}")
                results['errors'] += 1

        threads = []
        for doc in users_docs:
            t = threading.Thread(target=process_user, args=(doc.id,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=25)

        logger.info(f"Morning briefings done: {results}")
        return results

    except Exception as e:
        logger.error(f"Admin morning briefing trigger error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/files", tags=["Debug"])
async def debug_files(user: dict = Depends(verify_admin)):
    """Debug endpoint to list files in data directories."""
    import os

    paths_to_check = [
        "/app/data",
        "/app/outputs",
        os.path.join(os.getcwd(), "data"),
        os.path.join(os.getcwd(), "backend", "data"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    ]

    results = {}

    for path in paths_to_check:
        if os.path.exists(path):
            try:
                items = os.listdir(path)
                results[path] = items

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

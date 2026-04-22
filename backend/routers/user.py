from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from firebase_admin import auth
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from auth_middleware import verify_token
import firestore_manager as db_manager
from logger import logger

router = APIRouter(prefix="", tags=["User"])

limiter = Limiter(key_func=get_remote_address)


class UserProfile(BaseModel):
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    gender: Optional[str] = None
    resting_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None


class TokenRequest(BaseModel):
    token: str


class FeedbackSubmission(BaseModel):
    category: str  # "bug", "feature_request", "general"
    message: str
    page: Optional[str] = None


@router.get("/profile")
@limiter.limit("20/minute")
async def get_profile_endpoint(request: Request, user: dict = Depends(verify_token)):
    """Get the authenticated user's physical profile."""
    try:
        profile = db_manager.get_user_profile(user['uid'])
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile")
@limiter.limit("10/minute")
async def update_profile_endpoint(profile: UserProfile, request: Request, user: dict = Depends(verify_token)):
    """Update the user's physical profile."""
    try:
        data = {k: v for k, v in profile.model_dump().items() if v is not None}

        if db_manager.update_user_profile(user['uid'], data):
            return {"status": "success", "message": "Profile updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update profile")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/token")
@limiter.limit("5/minute")
async def register_fcm_token(token_req: TokenRequest, request: Request, user: dict = Depends(verify_token)):
    """Registers or updates the user's FCM token for push notifications."""
    try:
        success = db_manager.save_fcm_token(user['uid'], token_req.token)
        if success:
            return {"status": "success", "message": "FCM token registered"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/fcm-token")
@limiter.limit("10/minute")
async def save_fcm_token(request: Request, user: dict = Depends(verify_token)):
    """Save or update the user's FCM push notification token (legacy endpoint)."""
    uid = user['uid']
    try:
        body = await request.json()
        token = body.get('token', '')
        if not token:
            raise HTTPException(status_code=400, detail="FCM token is required")
        db_manager.save_fcm_token(uid, token)
        return {"status": "ok", "message": "FCM token saved"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FCM token save error for uid={uid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/account")
@limiter.limit("2/minute")
async def delete_account_endpoint(request: Request, user: dict = Depends(verify_token)):
    """
    Permanently delete the user account and all associated data.
    Complies with GDPR "Right to Erasure".
    """
    try:
        uid = user['uid']

        if not db_manager.delete_all_user_data(uid):
            raise HTTPException(status_code=500, detail="Failed to delete user data")

        try:
            auth.delete_user(uid)
            logger.info("User Account Deleted Permanently", extra={"event": "security_account_deletion", "uid": uid})
        except Exception as auth_error:
            logger.error(f"Auth Deletion Error: {auth_error}")
            raise HTTPException(status_code=500, detail="Failed to delete authentication user")

        return {"status": "success", "message": "Account deleted permanently"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/export")
@limiter.limit("3/hour")
async def export_user_data(request: Request, user: dict = Depends(verify_token)):
    """Exports all user data as JSON (GDPR compliance)."""
    try:
        uid = user['uid']

        export_data = {
            "user_id": uid,
            "exported_at": datetime.now().isoformat(),
            "goals": db_manager.get_all_goals(uid),
            "workouts": db_manager.get_all_workouts(uid, limit=1000),
            "plans": db_manager.get_recent_plans(uid, limit=100),
            "profile": db_manager.get_user_profile(uid)
        }

        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f"attachment; filename=health_ai_data_{uid}.json"
            }
        )
    except Exception as e:
        logger.error(f"Export Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
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
        logger.error(f"Feedback Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import Dict, Any, Optional
import threading
import uuid
import time as _time

from auth_middleware import verify_token, verify_admin
from encryption_helper import decrypt_password
import firestore_manager as db_manager
from logger import logger

router = APIRouter(prefix="/garmin", tags=["Garmin"])

limiter = Limiter(key_func=get_remote_address)

# In-memory MFA session store
_garmin_mfa_sessions: Dict[str, Any] = {}
_sessions_lock = threading.Lock()

# Throttling & Concurrency protection
_garmin_throttle_cache: Dict[str, float] = {}
_active_garmin_logins: set = set()

MFA_SESSION_TTL_SECONDS = 600  # 10 minutes


class GarminCredentials(BaseModel):
    username: str
    password: str


class GarminConnectRequest(BaseModel):
    username: str
    password: str


class GarminMfaRequest(BaseModel):
    session_id: str
    mfa_code: str


def check_garmin_cooldown(uid: str) -> Optional[float]:
    """Check if user is in Garmin rate-limit cooldown.
    Returns remaining seconds or None. Checks in-memory first, then Firestore."""
    now = _time.time()
    expiry = _garmin_throttle_cache.get(uid, 0)
    if now < expiry:
        return expiry - now
    try:
        creds_doc = db_manager.get_db().collection('users').document(uid) \
            .collection('garmin_credentials').document('default').get()
        if creds_doc.exists:
            rate_limit_until = creds_doc.to_dict().get('rate_limit_until')
            if rate_limit_until:
                expiry_ts = rate_limit_until.timestamp() if hasattr(rate_limit_until, 'timestamp') else float(rate_limit_until)
                if now < expiry_ts:
                    _garmin_throttle_cache[uid] = expiry_ts
                    return expiry_ts - now
    except Exception as e:
        logger.warning(f"Failed to check Garmin cooldown from Firestore: {e}")
    return None


def set_garmin_cooldown(uid: str, duration_seconds: int = 3600):
    """Set Garmin cooldown both in-memory and in Firestore (survives restarts)."""
    expiry = _time.time() + duration_seconds
    _garmin_throttle_cache[uid] = expiry
    try:
        from datetime import datetime, timezone
        expiry_dt = datetime.fromtimestamp(expiry, tz=timezone.utc)
        db_manager.get_db().collection('users').document(uid) \
            .collection('garmin_credentials').document('default') \
            .set({'rate_limit_until': expiry_dt}, merge=True)
        logger.info(f"🛡️ Garmin cooldown persisted to Firestore for {uid} until {expiry_dt.isoformat()}")
    except Exception as e:
        logger.warning(f"Failed to persist Garmin cooldown to Firestore: {e}")


def _save_garmin_tokens(garmin_client, uid: str) -> bool:
    """Saves garmin native tokens to Firestore after a successful login."""
    try:
        import sys
        import os
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        from fetch_garmin_data import save_garmin_session
        return save_garmin_session(uid, garmin_client)
    except Exception as e:
        logger.error(f"Failed to load shared save_garmin_session: {e}")
        return False


def _purge_expired_sessions():
    """Remove sessions older than TTL."""
    now = _time.time()
    with _sessions_lock:
        expired = [sid for sid, s in _garmin_mfa_sessions.items()
                   if s["expires_at"] < now]
        for sid in expired:
            del _garmin_mfa_sessions[sid]
            logger.info(f"🗑️ Purged expired Garmin MFA session {sid}")


@router.post("/credentials")
@limiter.limit("20/hour")
async def save_garmin_credentials_endpoint(
    request: Request,
    credentials: GarminCredentials,
    user: dict = Depends(verify_token)
):
    """
    Saves encrypted Garmin credentials for the authenticated user.

    Security:
    - Password is encrypted before storage using AES-256
    - Rate limited to 20 requests per hour
    """
    logger.info(f"💾 Saving Garmin credentials for user {user['uid']}")
    try:
        success = db_manager.save_garmin_credentials(
            user['uid'],
            credentials.username,
            credentials.password
        )

        if success:
            return {"status": "success", "message": "Garmin credentials saved securely"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save credentials")

    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Server configuration error: {str(e)}")
    except Exception as e:
        logger.error(f"Save Garmin Credentials Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
@limiter.limit("10/hour")
async def test_garmin_credentials_endpoint(
    request: Request,
    credentials: GarminCredentials,
    user: dict = Depends(verify_token)
):
    """Tests Garmin credentials without saving them."""
    try:
        from garminconnect import Garmin
        client = Garmin(credentials.username, credentials.password)
        client.login()
        return {"status": "success", "message": "Credentials verified successfully"}
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg:
            raise HTTPException(status_code=429, detail=f"Garmin has rate-limited your login attempts. Please wait 15-30 minutes. Error: {err_msg}")
        logger.warning(f"Garmin Test Failed for {user['uid']}: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed. Please check your username and password.")


@router.post("/connect")
@limiter.limit("3/minute")
async def garmin_connect(
    req: GarminConnectRequest,
    request: Request,
    user: dict = Depends(verify_token),
):
    """Start Garmin login."""
    uid = user["uid"]

    import sys
    import os
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from fetch_garmin_data import patch_garmin_client
    patch_garmin_client()

    remaining = check_garmin_cooldown(uid)
    if remaining:
        wait_min = int(remaining / 60) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Garmin has recently rate-limited your account. Please wait {wait_min} minutes before trying again."
        )

    now = _time.time()
    with _sessions_lock:
        if uid in _active_garmin_logins:
            raise HTTPException(
                status_code=409,
                detail="A login attempt is already in progress. Please wait."
            )
        _active_garmin_logins.add(uid)

    _purge_expired_sessions()

    try:
        from garminconnect import Garmin
        import tempfile
        import json as _json

        # Save credentials EARLY so they persist even if login fails
        db_manager.save_garmin_credentials(uid, req.username, req.password)
        logger.info(f"💾 Garmin credentials saved early for uid={uid}")

        # Try token-based resume FIRST
        token_resume_succeeded = False
        try:
            logger.info(f"🔑 Attempting direct token-based Garmin session resume for {uid}...")
            import json as _json2

            garth_token_files = None
            garth_legacy_token = None
            try:
                creds_raw = db_manager.get_db().collection('users').document(uid) \
                    .collection('garmin_credentials').document('default').get()
                if creds_raw.exists:
                    creds_data = creds_raw.to_dict()
                    enc = creds_data.get('garth_token_files_encrypted')
                    if enc:
                        try:
                            decrypted = decrypt_password(enc)
                            garth_token_files = _json2.loads(decrypted)
                        except Exception as dec_err:
                            logger.warning(f"⚠️ Token decryption/parse failed for {uid}: {dec_err}. Falling back to fresh login.")
                            garth_token_files = None
                    elif creds_data.get('garth_tokens'):
                        garth_legacy_token = creds_data['garth_tokens']
                        logger.info("🔑 Found legacy single garth token")
            except Exception as tf_err:
                logger.warning(f"⚠️ Could not load garth tokens from Firestore: {tf_err}")

            if garth_token_files or garth_legacy_token:
                token_client = Garmin(req.username, req.password)

                token_json_str = None
                if garth_token_files and '"di_token"' in _json2.dumps(garth_token_files):
                    token_json_str = _json2.dumps(garth_token_files)
                elif garth_legacy_token and isinstance(garth_legacy_token, dict):
                    logger.info("Ignoring legacy garth tokens in main connect, will proceed to fresh login if needed")

                if token_json_str:
                    logger.info("Loading saved native tokens into client...")
                    token_client.login(token_json_str)

                try:
                    logger.info("Testing Garmin session with lightweight API call...")
                    from datetime import date as _date
                    token_client.get_user_summary(_date.today().isoformat())
                    logger.info(f"✅ Garmin session is valid! Connected via token resume for uid={uid}")
                    _save_garmin_tokens(token_client, uid)
                    token_resume_succeeded = True
                    return {"status": "connected"}
                except Exception as api_err:
                    logger.warning(f"⚠️ Token resume API test failed for {uid}: {api_err}. Will attempt fresh login fallback.")
            else:
                logger.info(f"ℹ️ No valid saved tokens found for {uid}. Proceeding to fresh login.")

        except Exception as token_err:
            logger.info(f"ℹ️ Token resume structurally failed for {uid}: {token_err}. Proceeding to fresh login.")

        if token_resume_succeeded:
            return {"status": "connected"}

        # Fresh password login (only if token resume failed)
        tmp_session_dir = tempfile.mkdtemp(prefix=f"garmin_session_{uid}_")

        mfa_event = threading.Event()
        mfa_code_holder: Dict[str, str] = {}
        code_event = threading.Event()
        mfa_code_holder["_event"] = code_event

        def mfa_callback() -> str:
            logger.info(f"🔐 Garmin MFA requested for uid={uid}")
            mfa_event.set()
            code_event.wait(timeout=MFA_SESSION_TTL_SECONDS)
            return mfa_code_holder.get("code", "")

        garmin_client = Garmin(req.username, req.password)
        garmin_client.prompt_mfa = mfa_callback

        login_result: Dict[str, Any] = {}
        login_exception: Dict[str, Any] = {}

        def do_login():
            try:
                garmin_client.login()
                login_result["done"] = True
                logger.info(f"✅ Garmin login thread finished for uid={uid}")
            except Exception as exc:
                login_exception["error"] = exc
                logger.error(f"❌ Garmin login thread error for uid={uid}: {exc}")

        login_thread = threading.Thread(target=do_login, daemon=True)
        login_thread.start()

        login_thread.join(timeout=20)

        # Case 1: MFA required
        if mfa_event.is_set() and not login_result.get("done"):
            session_id = str(uuid.uuid4())
            with _sessions_lock:
                _garmin_mfa_sessions[session_id] = {
                    "uid": uid,
                    "client": garmin_client,
                    "login_thread": login_thread,
                    "mfa_code_holder": mfa_code_holder,
                    "code_event": code_event,
                    "expires_at": _time.time() + MFA_SESSION_TTL_SECONDS,
                    "username": req.username,
                    "password": req.password,
                }
            logger.info(f"🔐 2FA required for uid={uid}, session={session_id}")
            return {"status": "mfa_required", "session_id": session_id}

        # Case 2: Login exception
        if login_exception.get("error"):
            raise login_exception["error"]

        # Case 3: Login succeeded without MFA
        db_manager.save_garmin_credentials(uid, req.username, req.password)
        _save_garmin_tokens(garmin_client, uid)

        logger.info(f"✅ Garmin connected (no 2FA) for uid={uid}")
        return {"status": "connected"}

    except Exception as e:
        import traceback
        err_msg = str(e)
        logger.error(f"❌ Garmin connect error for uid={uid}: {err_msg}")
        logger.error(traceback.format_exc())

        if "429" in err_msg:
            logger.warning(f"⚠️ Garmin 429 (Rate Limit) hit for {uid}. No lockout applied.")
            raise HTTPException(
                status_code=429,
                detail=f"Garmin is rate-limiting requests. Original error: {err_msg}"
            )

        raise HTTPException(status_code=400, detail=f"Garmin connect failed: {err_msg}")
    finally:
        with _sessions_lock:
            _active_garmin_logins.discard(uid)


@router.post("/connect/mfa")
@limiter.limit("10/minute")
async def garmin_connect_mfa(
    req: GarminMfaRequest,
    request: Request,
    user: dict = Depends(verify_token),
):
    """Complete Garmin 2FA login by supplying the MFA code."""
    uid = user["uid"]

    with _sessions_lock:
        session = _garmin_mfa_sessions.get(req.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="MFA session not found or expired. Please start login again.")

    if session["uid"] != uid:
        raise HTTPException(status_code=403, detail="Session does not belong to this user.")

    if _time.time() > session["expires_at"]:
        with _sessions_lock:
            _garmin_mfa_sessions.pop(req.session_id, None)
        raise HTTPException(status_code=410, detail="MFA session expired. Please start login again.")

    try:
        session["mfa_code_holder"]["code"] = req.mfa_code.strip()
        session["code_event"].set()
        logger.info(f"🔐 MFA code submitted for session {req.session_id}, waiting for garth...")

        session["login_thread"].join(timeout=45)

        garmin_client = session["client"]
        username = session["username"]
        password = session["password"]

        if session["login_thread"].is_alive():
            raise ValueError("Garmin login is taking too long. Please try again.")

        db_manager.save_garmin_credentials(uid, username, password)
        _save_garmin_tokens(garmin_client, uid)

        with _sessions_lock:
            _garmin_mfa_sessions.pop(req.session_id, None)

        logger.info(f"✅ Garmin 2FA completed for uid={uid}")
        return {"status": "connected"}

    except Exception as e:
        logger.error(f"❌ Garmin MFA completion error for uid={uid}: {e}")
        with _sessions_lock:
            _garmin_mfa_sessions.pop(req.session_id, None)
        raise HTTPException(status_code=400, detail=f"MFA verification failed: {str(e)}")


@router.get("/status")
@limiter.limit("30/minute")
async def garmin_status(request: Request, user: dict = Depends(verify_token)):
    """Returns whether the user has a connected Garmin account."""
    uid = user["uid"]
    try:
        creds = db_manager.get_garmin_credentials(uid)
        if creds:
            return {"connected": True, "username": creds.get("username")}
        return {"connected": False, "username": None}
    except Exception as e:
        logger.error(f"❌ Garmin status error for uid={uid}: {e}")
        return {"connected": False, "username": None}


@router.delete("/credentials")
@limiter.limit("5/minute")
async def garmin_disconnect(request: Request, user: dict = Depends(verify_token)):
    """Disconnects the Garmin account by deleting stored credentials and tokens."""
    uid = user["uid"]
    try:
        db_manager.delete_garmin_credentials(uid)
        logger.info(f"🔌 Garmin disconnected for uid={uid}")
        return {"status": "success", "message": "Garmin account disconnected"}
    except Exception as e:
        logger.error(f"❌ Garmin disconnect error for uid={uid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-cooldown")
async def garmin_clear_cooldown(user: dict = Depends(verify_admin)):
    """Admin-only: Clear Garmin rate-limit cooldown so user can retry immediately."""
    uid = user["uid"]
    _garmin_throttle_cache.pop(uid, None)
    try:
        from google.cloud.firestore_v1 import DELETE_FIELD
        db_manager.get_db().collection('users').document(uid) \
            .collection('garmin_credentials').document('default') \
            .update({'rate_limit_until': DELETE_FIELD})
    except Exception as e:
        logger.warning(f"Firestore cooldown clear failed: {e}")

    logger.info(f"🔓 Garmin cooldown cleared for uid={uid}")
    return {"status": "success", "message": "Garmin cooldown cleared. You can retry immediately."}

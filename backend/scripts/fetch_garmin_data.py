import os
from datetime import date, timedelta

from garminconnect import Garmin
from dotenv import load_dotenv
import pandas as pd
from typing import List, Dict, Any, Optional
import sys

# Ensure backend path is in sys.path for firestore_manager
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from logger import logger



class GarminMFARequiredError(ValueError):
    """
    Raised when Garmin demands 2FA during an automated sync.
    The user must re-connect their Garmin account via the app to refresh tokens.
    """
    pass


def get_garmin_client(user_id: Optional[str] = None) -> Garmin:
    """
    Authenticate to Garmin using credentials.
    
    Uses garth token storage in Firestore to avoid the
    'OAuth1 token is required for OAuth2 refresh' error.
    Fresh login is only done when no valid token exists.
    
    Args:
        user_id: Firebase UID. If provided, uses encrypted credentials from Firestore.
                 If None, falls back to GARMIN_EMAIL/GARMIN_PASSWORD from .env (legacy).
    
    Returns:
        Authenticated Garmin client
        
    Raises:
        GarminMFARequiredError: If 2FA is required but no session is available
                                (user must reconnect via the app).
        ValueError: If credentials not found or authentication fails
    """
    email = None
    password = None
    
    if user_id:
        # NEW: Per-user credentials from Firestore
        try:
            import firestore_manager
            
            creds = firestore_manager.get_garmin_credentials(user_id)
            if creds:
                email = creds['username']
                password = creds['password']
                logger.info(f"✅ Using Garmin credentials for user: {user_id}")
            else:
                raise ValueError(f"No Garmin credentials found for user: {user_id}. Please connect your Garmin account in Profile settings.")
        except Exception as e:
            logger.error(f"❌ Failed to load Garmin credentials for user {user_id}: {e}")
            raise ValueError(f"Could not load Garmin credentials: {str(e)}")
    else:
        # LEGACY: Environment variables (for backward compatibility)
        load_dotenv()
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")
        
        if not email or not password:
            raise ValueError("No user_id provided and GARMIN_EMAIL/GARMIN_PASSWORD not set in environment. Please provide user_id or configure legacy credentials.")
        
        logger.warning(f"⚠️  Using legacy GARMIN_EMAIL from environment: {email}")

    # Authenticate using garth token if available, otherwise fresh login
    try:
        import garth
        import tempfile
        import json

        def _mfa_not_supported() -> str:
            """
            MFA callback used for background/automated sync calls.
            If this is triggered it means saved tokens have expired and
            the user needs to reconnect via the app (interactive 2FA).
            """
            raise GarminMFARequiredError(
                "Garmin 2FA is required but cannot be completed automatically. "
                "Please reconnect your Garmin account in the app settings to refresh your session."
            )

        client = Garmin(email, password, prompt_mfa=_mfa_not_supported)

        # Try to load saved garth tokens from Firestore
        garth_tokens = None
        if user_id:
            try:
                import firestore_manager
                creds_doc = firestore_manager.get_garmin_credentials(user_id)
                if creds_doc and 'garth_tokens' in creds_doc:
                    garth_tokens = creds_doc['garth_tokens']
                    logger.info("🔑 Found saved garth tokens, attempting token-based login...")
            except Exception as e:
                logger.warning(f"⚠️ Could not load garth tokens: {e}")

        if garth_tokens:
            # Resume session using saved tokens (avoids full re-login + OAuth1 issue)
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Try multi-file format first (new: stores exactly what garth.dump() wrote)
                    token_files_json = None
                    if user_id:
                        try:
                            import firestore_manager
                            from encryption_helper import decrypt_password
                            creds_raw = firestore_manager.db.collection('users').document(user_id)\
                                .collection('garmin_credentials').document('default').get()
                            if creds_raw.exists:
                                enc = creds_raw.to_dict().get('garth_token_files_encrypted')
                                if enc:
                                    token_files_json = json.loads(decrypt_password(enc))
                                    logger.info(f"🔑 Loaded multi-file tokens: {list(token_files_json.keys())}")
                        except Exception as mf_err:
                            logger.debug(f"Multi-file token load skipped: {mf_err}")

                    if token_files_json:
                        # Restore ALL files garth originally wrote
                        for fname, fdata in token_files_json.items():
                            with open(os.path.join(tmpdir, fname), "w") as f:
                                json.dump(fdata, f)
                    else:
                        # Legacy: single oauth2_token dict
                        token_file = os.path.join(tmpdir, "oauth2_token.json")
                        with open(token_file, "w") as f:
                            json.dump(garth_tokens, f)

                    client.garth.load(tmpdir)
                logger.info("✅ Garmin session resumed from saved tokens")
                
                return client
            except GarminMFARequiredError:
                raise  # Propagate clearly
            except Exception as token_err:
                # Tokens are present but couldn't be used (wrong format, expired, etc.)
                # Do NOT fall back to fresh login — that would trigger 2FA again.
                # Tell the user to reconnect interactively.
                logger.warning(f"⚠️ Token resume failed for uid={user_id}: {token_err}")
                raise GarminMFARequiredError(
                    "Your Garmin session has expired. "
                    "Please reconnect your Garmin account in the app settings to refresh your session."
                )


        # No saved tokens at all → attempt fresh login
        # (Only reaches here on first-ever connect without tokens)
        # Will raise GarminMFARequiredError via _mfa_not_supported if 2FA triggered
        client.login()
        logger.info(f"✅ Garmin login successful for: {email}")

        # Save garth tokens to Firestore for next time
        if user_id:
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    client.garth.dump(tmpdir)
                    token_file = os.path.join(tmpdir, "oauth2_token.json")
                    if os.path.exists(token_file):
                        with open(token_file, "r") as f:
                            tokens = json.load(f)
                        import firestore_manager
                        firestore_manager.save_garmin_tokens(user_id, tokens)
                        logger.info("💾 Garth tokens saved to Firestore")
            except Exception as save_err:
                logger.warning(f"⚠️ Could not save garth tokens: {save_err}")

        # Fix: Ensure display_name is populated regardless of how we authenticated
        if not getattr(client, "display_name", None):
            # 1. Try to get it from cached garth profile to avoid unnecessary/failing API calls
            try:
                if hasattr(client.garth, "profile") and isinstance(client.garth.profile, dict):
                    client.display_name = client.garth.profile.get("displayName")
                    client.full_name = client.garth.profile.get("fullName")
                    if client.display_name:
                        logger.info(f"Populated Garmin display_name from cache: {client.display_name}")
            except Exception as cache_err:
                logger.debug(f"Failed to read display_name from cache: {cache_err}")

            # 2. If still missing, attempt the API fetch as a last resort
            if not getattr(client, "display_name", None):
                try:
                    logger.debug("Fetching Garmin profile via API to populate missing display_name...")
                    prof = client.garth.connectapi("/userprofile-service/userprofile/profile")
                    if prof and isinstance(prof, dict):
                        client.display_name = prof.get("displayName")
                        client.full_name = prof.get("fullName")
                        logger.info(f"Populated Garmin display_name via API: {client.display_name}")
                except Exception as prof_err:
                    logger.warning(f"Failed to populate display_name via API: {prof_err}")
                    # Do NOT raise GarminMFARequiredError here! 
                    # If this endpoint is blocked (403) for non-MFA users, raising an error would break their sync forever.
                    # We simply log it. If the next API call (daily summary) fails, it will be caught later.

        # 3. Ultimate Fallback: Scrape the original payload or use a safe default
        if not getattr(client, "display_name", None):
            logger.error("🛑 ALL methods to retrieve display_name failed. Attempting deep scrape...")
            try:
                # Garth creates a 'profile' property, but the underlying JSON might have nested structures
                if hasattr(client.garth, "profile") and client.garth.profile:
                    logger.debug(f"DEBUG PROFILE DUMP: {client.garth.profile}")
            except Exception as e:
                pass
            
            # If we still have nothing, we must inject *something* to avoid `/None` crash
            # Often the username or email works as a fallback identifier for Garmin APIs
            fallback_name = getattr(client.garth, "username", email)
            if fallback_name and "@" in fallback_name:
                fallback_name = fallback_name.split("@")[0] # Best effort
            
            client.display_name = fallback_name or "unknown"
            logger.warning(f"⚠️ Forcing display_name to fallback value: {client.display_name}")

        # 4. Bulletproof Runtime Patch
        # Prevent `display_name=None` from EVER reaching the URL string in get_user_summary
        original_get_user_summary = client.get_user_summary
        def safe_get_user_summary(cdate: str) -> dict:
            if not getattr(client, "display_name", None):
                fallback = getattr(client.garth, "username", "unknown")
                if fallback and "@" in fallback:
                    fallback = fallback.split("@")[0]
                client.display_name = fallback or "unknown"
                logger.warning(f"Runtime Patch: Forced display_name to {client.display_name} right before API call.")
            return original_get_user_summary(cdate)
            
        client.get_user_summary = safe_get_user_summary
        client.get_stats = safe_get_user_summary

        return client
    except GarminMFARequiredError:
        raise  # Do not wrap – let the caller handle it
    except Exception as e:
        logger.error(f"❌ Garmin authentication failed: {e}")
        raise ValueError(f"Garmin login failed. Please check your credentials. Error: {str(e)}")





def fetch_daily_summary(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch daily summary data between start and end dates (inclusive)."""
    days = (end - start).days + 1
    records = []

    for i in range(days):
        d = start + timedelta(days=i)
        iso = d.isoformat()
        data = client.get_stats(iso)
        if not data:
            continue
        data["date"] = iso
        records.append(data)

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)

import concurrent.futures

def fetch_daily_heart_rate(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch intraday heart rate data between start and end dates (Parallelized)."""
    days = (end - start).days + 1
    records: List[Dict[str, Any]] = []
    
    date_list = [start + timedelta(days=i) for i in range(days)]

    def fetch_single_day_hr(d):
        iso = d.isoformat()
        try:
            hr_data = client.get_heart_rates(iso)
            if hr_data:
                return {"date": iso, "raw_hr_data": hr_data}
        except Exception as e:
            logger.error(f"Failed to get HR data for {iso}: {e}")
        return None

    # Use ThreadPoolExecutor for parallel processing
    # Cap workers to avoid overwhelming Garmin API (unofficial)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_single_day_hr, date_list))
    
    records = [r for r in results if r]

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def fetch_sleep_data(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch daily sleep data between start and end dates (Parallelized)."""
    days = (end - start).days + 1
    records: List[Dict[str, Any]] = []

    date_list = [start + timedelta(days=i) for i in range(days)]

    def fetch_single_day_sleep(d):
        iso = d.isoformat()
        try:
            sleep_data = client.get_sleep_data(iso)
            if sleep_data:
                return {"date": iso, "raw_sleep_data": sleep_data}
        except Exception as e:
            logger.error(f"Failed to get sleep data for {iso}: {e}")
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_single_day_sleep, date_list))
    
    records = [r for r in results if r]

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def fetch_activities(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch activities between start and end dates (Batch mode)."""
    records: List[Dict[str, Any]] = []
    
    start_iso = start.isoformat()
    end_iso = end.isoformat()
    
    try:
        # Optimized: Batch fetch using date range
        logger.info(f"Fetching activities from {start_iso} to {end_iso}...")
        activities = client.get_activities_by_date(start_iso, end_iso, "") # type assumption
        
        if activities:
            for activity in activities:
                # Add fetch_date for consistency, though process_garmin_data uses startTimeLocal
                # Use startTimeLocal as fetch_date proxy or just today's date? 
                # Original code used the loop date. Here we use the activity's actual date.
                if 'startTimeLocal' in activity:
                    activity["fetch_date"] = activity['startTimeLocal'].split(' ')[0]
                else:
                    activity["fetch_date"] = start_iso # Fallback
                records.append(activity)
                
    except Exception as e:
         logger.error(f"Failed to batch fetch activities: {e}")
         # Fallback? No, if batch fails, we likely have bigger issues.

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def get_latest_date(filename):
    """Returns the latest date found in the CSV, or None."""
    if not os.path.exists(filename):
        return None
    try:
        df = pd.read_csv(filename)
        if 'date' in df.columns:
            return pd.to_datetime(df['date']).max().date()
        if 'calendarDate' in df.columns:
            return pd.to_datetime(df['calendarDate']).max().date()
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return None

def update_csv(new_df, filename, key_col='date'):
    """Updates existing CSV with new data, handling duplicates."""
    if new_df is None or new_df.empty:
        return

    if os.path.exists(filename):
        try:
            old_df = pd.read_csv(filename)
            combined = pd.concat([old_df, new_df], ignore_index=True)
            combined = combined.drop_duplicates(subset=[key_col], keep='last')
            combined.to_csv(filename, index=False)
            combined.to_csv(filename, index=False)
            logger.info(f"Updated {filename}: Added {len(new_df)} new rows (Total: {len(combined)})")
        except Exception as e:
            logger.error(f"Error updating {filename}: {e}. Overwriting...")
            new_df.to_csv(filename, index=False)
    else:
        new_df.to_csv(filename, index=False)
        logger.info(f"Created {filename} with {len(new_df)} rows")

def main(user_id: Optional[str] = None, mode: str = "incremental"):
    """
    Fetches Garmin data for a specific user or uses legacy mode.
    Mode 'incremental' overlaps 1 day, 'full' overlaps 5 days.
    """
    client = get_garmin_client(user_id)

    today = date.today()
    
    # Determine data directory path robustly
    script_dir = os.path.dirname(os.path.abspath(__file__)) # .../backend/scripts
    backend_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(backend_dir)
    
    def get_data_dir(uid: Optional[str] = None):
        # 1. Base data path relative to this script
        # Script is in .../backend/scripts/
        # Data is in .../backend/data/ (or /app/data in Docker)
        
        # Robust path resolution
        if os.path.exists("/app/data"):
            base_path = "/app/data"
        else:
            # Local: .../backend/data
            base_path = os.path.join(backend_dir, "data")
            
        # 2. Append user_id if provided
        if uid:
            user_path = os.path.join(base_path, uid)
            return user_path
        
        return base_path

    data_dir = get_data_dir(user_id)
    os.makedirs(data_dir, exist_ok=True)
    logger.info(f"📁 Using data directory: {data_dir}")
    
    last_sync = get_latest_date(f"{data_dir}/garmin_daily_summary.csv")
    
    if last_sync:
        overlap_days = 1 if mode == "incremental" else 5
        start = last_sync - timedelta(days=overlap_days)
        logger.info(f"Found existing data up to {last_sync}. Fetching from {start} ({overlap_days}-day overlap) [{mode}]...")
    else:
        fallback_days = 7 if mode == "incremental" else 360
        start = today - timedelta(days=fallback_days)
        logger.info(f"No existing data. Fetching from {start} (fallback: {fallback_days} days) [{mode}]...")

    if start > today:
        logger.info("Data is already up to date!")
        return

    # 1. Summary
    df_summary = fetch_daily_summary(client, start, today)
    update_csv(df_summary, f"{data_dir}/garmin_daily_summary.csv")

    # 2. HR
    df_hr = fetch_daily_heart_rate(client, start, today)
    update_csv(df_hr, f"{data_dir}/garmin_hr_timeseries.csv")

    # 3. Sleep
    df_sleep = fetch_sleep_data(client, start, today)
    update_csv(df_sleep, f"{data_dir}/garmin_sleep_data.csv")

    # 4. Activities
    df_activities = fetch_activities(client, start, today)
    # Use 'activityId' as key if available, else 'date' (fallback)
    key = 'activityId' if (df_activities is not None and 'activityId' in df_activities.columns) else 'date'
    update_csv(df_activities, f"{data_dir}/garmin_activities.csv", key_col=key)

    # 5. Sync to Firestore (NEW: To power Weekly Load widget)
    if not df_activities.empty:
        logger.info(f"Syncing {len(df_activities)} activities to Firestore for Weekly Load...")
        import firestore_manager
        
        # Only sync if user_id is provided
        if user_id:
            for _, row in df_activities.iterrows():
                try:
                    activity_id = row.get('activityId')
                    if not activity_id:
                        continue
                    
                    # Map Garmin activity to Firestore workout schema
                    # Use 'activityTrainingLoad' as load_estimate, fallback to 0
                    load_est = row.get('activityTrainingLoad', 0)
                    if pd.isna(load_est):
                        load_est = 0
                        
                    workout_doc = {
                        "date": str(pd.to_datetime(row['startTimeLocal']).date()),
                        "activity": row.get('activityName', 'Garmin Activity'),
                        "duration_min": int(row.get('duration', 0) / 60),
                        "load_estimate": int(round(float(load_est))),
                        "status": "DONE",
                        "source": "GARMIN",
                        "garmin_activity_id": str(activity_id)
                    }
                    
                    firestore_manager.save_garmin_workout(user_id, workout_doc, activity_id)
                except Exception as sync_err:
                    logger.warning(f"⚠️ Failed to sync activity {activity_id} to Firestore: {sync_err}")
        else:
            logger.warning("⚠️ Skipping Firestore sync: No user_id provided (Legacy Mode)")
    
    # 6. NOTE: Daily summary metrics are synced to Firestore by process_garmin_data.py
    # This ensures calculated metrics (CTL/ATL/TSB) are included.

    logger.info(f"✅ Garmin data fetch completed for {'user: ' + user_id if user_id else 'legacy mode'}")

if __name__ == "__main__":
    main()

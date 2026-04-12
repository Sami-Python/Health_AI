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


def patch_garmin_client():
    """
    Universal Fix v4: Allows garminconnect 0.3.1's multi-strategy login
    but blocks plain-requests fallbacks that trigger Cloudflare detection.
    Also patches garth session for data fetching.
    """
    try:
        # 1. Patch garth (for session persistence and data fetching)
        import garth.http
        from curl_cffi import requests as curl_requests

        if "curl_cffi" not in str(type(garth.client.sess)):
            logger.info("🛡️ Patching garth singleton with curl_cffi")
            new_sess = curl_requests.Session(impersonate="chrome120")
            garth.client.sess = new_sess
            garth.http.client.sess = new_sess

        # 2. Patch garminconnect login to skip plain-requests strategies
        try:
            import garminconnect
            
            TargetClass = None
            if hasattr(garminconnect, 'Garmin'):
                TargetClass = garminconnect.Garmin
            elif hasattr(garminconnect, 'client') and hasattr(garminconnect.client, 'Client'):
                TargetClass = garminconnect.client.Client

            if not TargetClass:
                logger.warning("⚠️ Could not find Garmin client class to patch")
                return

            # Only patch once
            if getattr(TargetClass, '_v4_patched', False):
                return
            TargetClass._v4_patched = True

            original_login = TargetClass.login
            def patched_login(self, *args, **kwargs):
                """
                v4: Direct POST to Garmin SSO using curl_cffi and garth ticket exchange.
                Bypasses all front-end Cloudflare blocks completely by avoiding the sign-in page.
                """
                # Delegate to original token loading if provided (or arbitrary arguments)
                if (args and len(args) > 0 and args[0]) or kwargs.get('tokenstore'):
                    return original_login(self, *args, **kwargs)

                from curl_cffi import requests as cffi_requests
                import garth
                from garth.sso import exchange as garth_exchange
                
                logger.info("🔍 [v4] Starting Direct POST login...")
                session = cffi_requests.Session(impersonate="safari")
                resp = session.post(
                    "https://sso.garmin.com/portal/api/login",
                    params={
                        "clientId": "GCM_ANDROID_DARK",
                        "locale": "en-US",
                        "service": "https://mobile.integration.garmin.com/gcm/android",
                    },
                    json={
                        "username": getattr(self, "username", ""),
                        "password": getattr(self, "password", ""),
                        "rememberMe": False,
                        "captchaToken": "",
                    },
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Origin": "https://sso.garmin.com",
                        "Referer": "https://sso.garmin.com/portal/sso/en-US/sign-in",
                    },
                    timeout=15,
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    status_type = data.get("responseStatus", {}).get("type", "")
                    
                    if status_type == "SUCCESSFUL":
                        ticket = data.get("serviceTicketId", "")
                        logger.info(f"✅ Service ticket acquired from direct login! {ticket[:40]}...")
                        
                        # Exchange ticket for OAuth tokens natively
                        try:
                            client_to_use = self.garth if hasattr(self, 'garth') else garth.client
                            
                            # Custom OAuth1 exchange using the proper mobile login-url instead of sso/embed
                            from urllib.parse import parse_qs
                            from garth.sso import OAuth1Token, GarminOAuth1Session
                            
                            oauth_sess = GarminOAuth1Session(parent=client_to_use.sess)
                            base_url = f"https://connectapi.{client_to_use.domain}/oauth-service/oauth/"
                            login_url = "https://mobile.integration.garmin.com/gcm/android"
                            url = f"{base_url}preauthorized?ticket={ticket}&login-url={login_url}&accepts-mfa-tokens=true"
                            
                            logger.info(f"🔑 Exchanging for OAuth1 using mobile url...")
                            oauth1_resp = oauth_sess.get(
                                url,
                                headers={"User-Agent": "com.garmin.android.apps.connectmobile"},
                                timeout=client_to_use.timeout
                            )
                            oauth1_resp.raise_for_status()
                            parsed = parse_qs(oauth1_resp.text)
                            token_dict = {k: v[0] for k, v in parsed.items()}
                            oauth1 = OAuth1Token(domain=client_to_use.domain, **token_dict)

                            logger.info("✅ OAuth1 obtained")
                            oauth2 = garth_exchange(oauth1, client_to_use)
                            logger.info("✅ OAuth2 obtained! Access token generated.")
                        except Exception as e:
                            logger.error(f"Failed to exchange ticket: {e}")
                            if hasattr(e, 'response') and e.response is not None:
                                logger.error(f"Response: {e.response.text}")
                            raise

                        # Extract first part of email for fallback display_name
                        username = getattr(self, "username", "")
                        fallback_name = username.split("@")[0] if username and "@" in username else "unknown"
                        
                        # Inject the tokens
                        if hasattr(self, 'garth'):
                            self.garth.oauth1_token = oauth1
                            self.garth.oauth2_token = oauth2
                            self.garth._profile = {"displayName": fallback_name, "fullName": fallback_name}
                        else:
                            garth.client.oauth1_token = oauth1
                            garth.client.oauth2_token = oauth2
                        
                        if hasattr(self, 'client'):
                            self.client.di_token = oauth2.access_token
                        self.display_name = fallback_name
                        
                        logger.info("✅ Direct POST login completely successful! Tokens injected.")
                        return getattr(oauth1, "access_token", None), getattr(oauth2, "access_token", None)
                        
                    elif status_type == "MFA_REQUIRED":
                        import garminconnect
                        raise getattr(garminconnect, 'GarminConnectAuthenticationError', Exception)("MFA Required")
                    else:
                        import garminconnect
                        raise getattr(garminconnect, 'GarminConnectAuthenticationError', Exception)(f"Unexpected SSO type: {status_type}")
                elif resp.status_code in [401, 403]:
                    import garminconnect
                    raise getattr(garminconnect, 'GarminConnectAuthenticationError', Exception)(f"Invalid credentials (HTTP {resp.status_code})")
                elif resp.status_code == 429:
                    import garminconnect
                    raise getattr(garminconnect, 'GarminConnectTooManyRequestsError', Exception)("Rate limited")
                else:
                    import garminconnect
                    raise getattr(garminconnect, 'GarminConnectConnectionError', Exception)(f"Garmin SSO returned HTTP {resp.status_code}")

            TargetClass.login = patched_login
            logger.info("🛡️ garminconnect patched (v4): direct POST login strategy")

        except ImportError:
            logger.warning("⚠️ garminconnect not found, skipping v4 patch")

    except Exception as e:
        logger.error(f"❌ Failed to apply Garmin Universal Fix v4: {e}")


def save_garmin_session(user_id: str, client: Garmin) -> bool:
    """
    Saves garminconnect 0.2.x/0.3.x native tokens to Firestore robustly.
    """
    import json
    import firestore_manager
    from encryption_helper import encrypt_password

    if not user_id or not client:
        return False

    try:
        # Support both garminconnect >= 0.3.1 (client.client) and < 0.3.x (client.garth)
        inner_client = getattr(client, 'client', None) or getattr(client, 'garth', None)
        if not inner_client:
            logger.warning(f"⚠️ client missing inner garth/client object for {user_id}")
            return False

        import tempfile
        import os
        token_data = {}
        with tempfile.TemporaryDirectory() as tmpdir:
            inner_client.dump(tmpdir)
            # Read whatever files were dumped
            for f_name in os.listdir(tmpdir):
                if f_name.endswith('.json'):
                    with open(os.path.join(tmpdir, f_name), 'r') as f:
                        key = f_name.replace('.json', '')
                        token_data[key] = json.load(f)

        if not token_data or ("oauth1_token" not in token_data and "oauth2_token" not in token_data):
            # Check the base level for di_token if it's the newer format
            if "di_token" not in token_data:
                logger.warning(f"⚠️ dump() produced incomplete tokens for {user_id}: {token_data}")
                return False

        # 1. Save legacy single-token format for backward compatibility
        firestore_manager.save_garmin_tokens(user_id, token_data)

        # 2. Save encrypted
        encrypted = encrypt_password(token_str)
        firestore_manager.db.collection('users').document(user_id)\
            .collection('garmin_credentials').document('default')\
            .update({'garth_token_files_encrypted': encrypted})
        
        logger.info(f"💾 Garmin session tokens persisted for {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save garmin session: {e}")
        return False


def get_garmin_client(user_id: Optional[str] = None, allow_fresh: bool = True) -> Garmin:
    """
    Authenticate to Garmin using credentials and robust local token loading.
    Migrates old garth tokens gracefully.
    """
    email = None
    password = None
    
    if user_id:
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
        # LEGACY: Environment variables
        load_dotenv()
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")
        if not email or not password:
            raise ValueError("No user_id provided and GARMIN_EMAIL/GARMIN_PASSWORD not set in environment.")
        logger.warning(f"⚠️ Using legacy GARMIN_EMAIL from environment: {email}")

    # Apply the curl_cffi monkeypatch before creating the client
    patch_garmin_client()
    
    try:
        import json

        def _mfa_not_supported() -> str:
            raise GarminMFARequiredError(
                "Garmin 2FA is required but cannot be completed automatically. "
                "Please reconnect your Garmin account in the app settings to refresh your session."
            )

        # Use garminconnect 0.3.x logic with TLS impersonation (curl_cffi)
        # The new version handles Cloudflare/SSO much better.
        client = Garmin(email, password)
        
        # Override the MFA prompt if needed
        client.prompt_mfa = _mfa_not_supported
        
        # Step 0: Load and Decrypt Tokens
        token_json_str = None
        if user_id:
            try:
                import firestore_manager
                from encryption_helper import decrypt_password
                creds_raw = firestore_manager.db.collection('users').document(user_id)\
                    .collection('garmin_credentials').document('default').get()
                if creds_raw.exists:
                    enc = creds_raw.to_dict().get('garth_token_files_encrypted')
                    if enc:
                        try:
                            decrypted_str = decrypt_password(enc)
                            if '"di_token"' in decrypted_str or '"oauth1_token"' in decrypted_str or '"oauth2_token"' in decrypted_str:
                                token_json_str = decrypted_str
                                logger.info("🔑 Found saved native Garmin tokens")
                            else:
                                logger.warning(f"⚠️ Unrecognized token structure: {decrypted_str[:50]}")
                        except Exception as dec_err:
                            logger.warning(f"⚠️ Token decryption failed (likely corrupted): {dec_err}. Will proceed to fresh login.")
            except Exception as mf_err:
                logger.debug(f"Token load structurally failed: {mf_err}")

        try:
            # Universal compatibile loading using tempdir, as 0.2.x strictly requires directory path
            if token_json_str:
                import json
                import tempfile
                import os
                
                token_dict = json.loads(token_json_str)
                with tempfile.TemporaryDirectory() as tmpdir:
                    for k, v in token_dict.items():
                        # Garth looks for oauth1_token.json and oauth2_token.json
                        with open(os.path.join(tmpdir, f"{k}.json"), "w") as f:
                            json.dump(v, f)
                    
                    try:
                        client.login(tmpdir)
                    except Exception as try_dir_err:
                        logger.warning(f"⚠️ Tempdir login failed ({try_dir_err}), falling back to direct string for 0.3.x+")
                        client.login(token_json_str)
            else:
                if not allow_fresh:
                    logger.warning(f"🛑 Background sync blocked: No saved tokens and allow_fresh=False for {user_id}")
                    raise ValueError("Garmin session expired. Please re-connect in settings.")
                client.login()
            
            logger.info("✅ Garmin login successful")
            if user_id:
                save_garmin_session(user_id, client)
        except Exception as e:
            err_msg = str(e)
            # If we had tokens and it failed (for any reason: 429, 401, expired), try a fresh login ONE time if allowed.
            if token_json_str:
                if not allow_fresh:
                    logger.warning(f"🛑 Background sync: Token login failed and allow_fresh=False. Error: {err_msg}")
                    raise ValueError("Garmin session expired. Please re-login in settings.")
                
                logger.warning(f"⚠️ Token-based login failed: {err_msg}. Attempting ONE fresh login fallback...")
                try:
                    # Force fresh login by clearing any internal tokens first
                    if hasattr(client, "garth") and client.garth:
                         # 0.3.x internal garth object
                         client.garth.dumpstore = None
                    
                    client.login() # Fresh login using username/pass from __init__
                    logger.info("✅ Garmin fresh login successful after token failure")
                    if user_id:
                        save_garmin_session(user_id, client)
                except Exception as fresh_err:
                    fresh_msg = str(fresh_err)
                    if "429" in fresh_msg:
                        logger.error(f"🛑 Fresh login also hit 429: {fresh_msg}")
                    raise ValueError(f"Garmin login failed. Please wait 30-60 mins if rate-limited. Error: {fresh_msg}")
            else:
                # Fresh login failed directly (or was blocked by not allow_fresh above)
                if "429" in err_msg:
                    logger.error(f"🛑 Fresh login hit 429: {err_msg}")
                    raise ValueError(f"Garmin rate-limited. Please wait 30-60 mins. Error: {err_msg}")
                raise ValueError(f"Garmin login failed: {err_msg}")

        # Ensure display name is fetched if not present.
        if not getattr(client, "display_name", None):
            try:
                # Try new profile endpoint first
                prof = client.connectapi("/userprofile-service/socialProfile")
                if prof and isinstance(prof, dict):
                    client.display_name = prof.get("displayName")
                    client.full_name = prof.get("fullName", "")
                    logger.info(f"Populated Garmin display_name: {client.display_name}")
            except Exception as prof_err:
                logger.warning(f"Failed to populate display_name via API: {prof_err}")

        # Ultimate fallback
        if not getattr(client, "display_name", None):
            fallback_name = getattr(client, "username", email)
            if fallback_name and "@" in fallback_name:
                fallback_name = fallback_name.split("@")[0]
            client.display_name = fallback_name or "unknown"

        # Bulletproof Runtime Patch
        original_get_user_summary = client.get_user_summary
        def safe_get_user_summary(cdate: str) -> dict:
            if not getattr(client, "display_name", None):
                fallback = getattr(client, "username", email)
                client.display_name = (fallback.split("@")[0] if fallback and "@" in fallback else "unknown")
            return original_get_user_summary(cdate)
            
        client.get_user_summary = safe_get_user_summary
        client.get_stats = safe_get_user_summary

        return client
    except GarminMFARequiredError:
        raise
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg:
             raise ValueError("Garmin has rate-limited your login attempts. Please wait 15-30 minutes.")
        raise ValueError(f"Garmin login failed. Error: {err_msg}")





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

def main(user_id: Optional[str] = None, mode: str = "incremental", allow_fresh: bool = True):
    """
    Fetches Garmin data for a specific user or uses legacy mode.
    Mode 'incremental' overlaps 1 day, 'full' overlaps 5 days.
    """
    client = get_garmin_client(user_id, allow_fresh=allow_fresh)

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
    
    if mode == "full":
        # Full Retrain: Fetch 180 days (half year) of history as requested
        start = today - timedelta(days=180)
        logger.info(f"🚀 Full Retrain mode: Fetching 180 days of history starting from {start}...")
    elif last_sync:
        # Incremental: Just fetch since last sync with a small overlap
        start = last_sync - timedelta(days=1)
        logger.info(f"🔄 Incremental mode: Found data up to {last_sync}. Fetching from {start}...")
    else:
        # Initial sync: Default to 7 days for quick start
        fallback_days = 7
        start = today - timedelta(days=fallback_days)
        logger.info(f"🆕 Initial sync: Fetching from {start} (fallback {fallback_days} days)...")

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

    # 7. Persistence: Save back the potentially refreshed tokens
    if user_id:
        save_garmin_session(user_id, client)

    logger.info(f"✅ Garmin data fetch completed for {'user: ' + user_id if user_id else 'legacy mode'}")

if __name__ == "__main__":
    main()

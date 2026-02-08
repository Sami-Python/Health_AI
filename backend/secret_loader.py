
import os
import json
from dotenv import load_dotenv

# Try importing Secret Manager (it might not be installed in minimal envs)
# This allows the code to run in basic dev environments without the heavy lib if needed
try:
    from google.cloud import secretmanager
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False

# Explicitly load .env from the backend directory
basedir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# Google Cloud Project ID (defaults to known project, can be overridden)
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "personal-ai-coach-92c39") 

def get_secret(secret_id, version_id="latest"):
    """
    Attempts to retrieve a secret string.
    Priority:
    1. Environment Variable (matching secret_id) - Great for Local Dev / Docker Env Override
    2. Google Secret Manager (if 'USE_SECRET_MANAGER' is true) - Best for Production
    3. Return None if not found
    """
    # 1. Env Var (Local Override)
    # This checks if the secret itself is set as an env var (e.g. GEMINI_API_KEY)
    env_val = os.getenv(secret_id)
    if env_val:
        return env_val
        
    # 2. Secret Manager
    if os.getenv("USE_SECRET_MANAGER", "false").lower() == "true":
        if not SECRET_MANAGER_AVAILABLE:
            print(f"Warning: USE_SECRET_MANAGER=true but google-cloud-secret-manager not installed. Cannot fetch {secret_id}.")
            return None
            
        try:
            client = secretmanager.SecretManagerServiceClient()
            # secrets are stored under projects/{project_id}/secrets/{secret_id}
            name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            # Don't crash, just log error and return None
            print(f"Error fetching secret '{secret_id}' from Secret Manager: {e}")
            return None
            
    return None

def get_service_account_dict():
    """
    Special helper for Firebase Credentials.
    Returns:
        dict: The parsed JSON content of the service account key.
        str: Attributes to a file path (if legacy path is used), though dict is preferred.
        None: If not found.
    """
    # 1. Env Var with JSON content (e.g. Docker/CI secret injection)
    # Variable name convention: FIREBASE_SERVICE_ACCOUNT_JSON
    json_str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print("Error: FIREBASE_SERVICE_ACCOUNT_JSON env var contains invalid JSON.")
            pass

    # 2. Secret Manager
    if os.getenv("USE_SECRET_MANAGER", "false").lower() == "true":
        # We assume the secret name is also 'FIREBASE_SERVICE_ACCOUNT_JSON' in Secret Manager
        data = get_secret("FIREBASE_SERVICE_ACCOUNT_JSON")
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                 print("Error: Secret Manager 'FIREBASE_SERVICE_ACCOUNT_JSON' contains invalid JSON.")
                 pass

    # 3. Env Var pointing to file (Legacy/Local)
    # Logic: If GOOGLE_APPLICATION_CREDENTIALS is set, return that PATH.
    # Firebase Admin can take the path directly.
    cred_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_file and os.path.exists(cred_file):
         return cred_file # Return path string
         
    # 4. Fallback to default local file in project
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(base_dir, "service_account_key.json")
    if os.path.exists(default_path):
        return default_path
        
    return None

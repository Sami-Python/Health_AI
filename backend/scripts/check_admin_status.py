import os
import sys
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import auth, credentials

# Ensure backend path is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Load environment variables
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

# Initialize Firebase Admin if not already
if not firebase_admin._apps:
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.path.join(BACKEND_DIR, 'service_account_key.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        print(f"Error: Could not find credentials at {cred_path}")
        sys.exit(1)

def check_user_admin(uid):
    print(f"Checking Admin Status for UID: {uid}")
    
    try:
        user = auth.get_user(uid)
        email = user.email
        print(f"User Email: {email}")
        
        admin_emails_env = os.getenv("ADMIN_EMAILS", "")
        admin_emails = [e.strip() for e in admin_emails_env.split(",") if e.strip()]
        
        print(f"Configured Admin Emails: {admin_emails}")
        
        if email in admin_emails:
            print("✅ Status: USER IS ADMIN")
        else:
            print("❌ Status: USER IS NOT ADMIN")
            print(f"   Action: Add '{email}' to ADMIN_EMAILS in .env and Cloud Run secrets.")
            
    except Exception as e:
        print(f"Error fetching user: {e}")

if __name__ == "__main__":
    UID = "wI0j4s1a9hZtGGaWtNnEn3yqSZC2"
    check_user_admin(UID)

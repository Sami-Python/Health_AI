import firebase_admin
from firebase_admin import auth, credentials
import os
import sys

# Initialize using the same logic as main.py (or simpler for this script)
# We need to setup the app to run this script standalone
try:
    # Try using service account file if it exists
    if os.path.exists('service_account_key.json'):
        cred = credentials.Certificate('service_account_key.json')
        firebase_admin.initialize_app(cred)
    else:
        # Fallback to default (might work if env vars set, but explicit is better)
        # Using the project ID from env or hardcoded for this quick script
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'personal-ai-coach-92c39')
        firebase_admin.initialize_app(options={'projectId': project_id})

    email = "sami@personalaicoach.ai"
    password = "password123"

    try:
        user = auth.get_user_by_email(email)
        print(f"User {email} already exists. UID: {user.uid}")
        # Update password to be sure
        auth.update_user(user.uid, password=password)
        print(f"Password updated to: {password}")

    except auth.UserNotFoundError:
        print(f"Creating user {email}...")
        user = auth.create_user(
            email=email,
            password=password,
            display_name="Sami Test"
        )
        print(f"User created successfully. UID: {user.uid}")

except Exception as e:
    print(f"Error: {e}")

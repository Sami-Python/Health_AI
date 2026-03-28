"""
Clear Garmin rate-limit cooldown from Firestore for a specific user.
Usage:  python clear_garmin_cooldown.py <firebase_uid>
"""
import sys, os

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from google.cloud import firestore


def clear_cooldown(uid: str):
    db = firestore.Client()
    doc_ref = db.collection('users').document(uid)\
        .collection('garmin_credentials').document('default')
    
    doc = doc_ref.get()
    if not doc.exists:
        print(f"No garmin_credentials doc found for uid={uid}")
        return
    
    data = doc.to_dict()
    rate_limit_until = data.get('rate_limit_until')
    
    if rate_limit_until:
        print(f"Current rate_limit_until: {rate_limit_until}")
        doc_ref.update({'rate_limit_until': firestore.DELETE_FIELD})
        print(f"✅ Cleared rate_limit_until for uid={uid}")
    else:
        print(f"No active cooldown found for uid={uid}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clear_garmin_cooldown.py <firebase_uid>")
        sys.exit(1)
    
    clear_cooldown(sys.argv[1])

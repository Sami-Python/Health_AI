import os
import sys

# Ensure backend path is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import firestore_manager
from encryption_helper import decrypt_password

def verify_encryption():
    print("Verifying Garmin Credential Encryption...\n")
    
    db = firestore_manager.get_db()
    users = db.collection('users').stream()
    
    found = False
    for user in users:
        uid = user.id
        creds_ref = db.collection('users').document(uid).collection('garmin_credentials').document('default')
        doc = creds_ref.get()
        
        if doc.exists:
            found = True
            data = doc.to_dict()
            username = data.get('username', 'UNKNOWN')
            encrypted = data.get('password_encrypted', '')
            
            print(f"User: {uid}")
            print(f"   Garmin Email: {username}")
            
            if encrypted:
                print(f"   Encrypted Blob: {encrypted[:15]}... (Length: {len(encrypted)})")
                
                # Verify we can decrypt it
                try:
                    decrypted = decrypt_password(encrypted)
                    if decrypted and len(decrypted) > 0:
                        print("   Decryption Check: SUCCESS (Password recovered)")
                    else:
                        print("   Decryption Check: FAILED (Empty result)")
                except Exception as e:
                    print(f"   Decryption Check: FAILED ({e})")
            else:
                print("   No encrypted password found!")
            print("-" * 40)
            
    if not found:
        print("No Garmin credentials found in Firestore.")
    else:
        print("\nVerification complete.")


if __name__ == "__main__":
    verify_encryption()

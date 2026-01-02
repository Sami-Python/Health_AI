from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
import os

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verifies the Firebase ID token included in the Authorization header.
    Returns the decoded token dictionary if valid, otherwise raises 401.
    """
    token = credentials.credentials
    try:
        # In development, we might want to bypass for testing if explicitly configured
        # But for 'production roadmap', we should enforce it.
        # Check for mock token in local dev if needed, but standard is force verify.
        
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

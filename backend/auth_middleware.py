from fastapi import HTTPException, Security, Request

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
import os
from logger import logger


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
        # Log security event: Authentication Failed
        logger.warning(
            "Authentication Failed", 
            extra={
                "event": "security_auth_failure",
                "error": str(e),
                "token_preview": token[:10] + "..." if token else "None"
            }
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

from fastapi import Depends

def verify_admin(user: dict = Depends(verify_token)):
    """
    Verifies that the authenticated user is an admin.
    Checked against ADMIN_EMAILS environment variable (comma separated).
    """
    admin_emails = os.getenv("ADMIN_EMAILS", "")
    user_email = user.get("email")
    
    if not user_email:
        logger.warning("Admin access denied: Email missing in token", extra={"event": "security_admin_denied", "uid": user.get("uid")})
        raise HTTPException(status_code=403, detail="Email required for admin access")

    if user_email not in admin_emails.split(","):
        logger.warning(
            "Admin access denied: Unauthorized email", 
            extra={
                "event": "security_admin_denied", 
                "email": user_email,
                "uid": user.get("uid")
            }
        )
        raise HTTPException(status_code=403, detail="Admin access denied")
    
    return user

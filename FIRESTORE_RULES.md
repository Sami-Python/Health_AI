# Firestore Security Rules - Deployment Guide

## Overview

This file contains row-level security rules for Cloud Firestore. These rules ensure that:
- Users can only access their own data
- All requests require authentication
- Admins have elevated permissions for feedback management

## Local Testing (Optional)

```bash
# Install Firebase emulator (if not already installed)
npm install -g firebase-tools

# Start Firestore emulator
firebase emulators:start --only firestore

# Test rules interactively
firebase emulators:start --only firestore --inspect-functions
```

## Deployment

### 1. Deploy via Firebase CLI

```bash
# From project root
firebase deploy --only firestore:rules
```

### 2. Deploy via Firebase Console (Manual)

1. Go to https://console.firebase.google.com/project/personal-ai-coach-92c39/firestore/rules
2. Copy contents of `firestore.rules`
3. Paste into editor
4. Click "Publish"

## Verification

After deployment, verify rules are working:

1. **Test with authenticated user:**
   ```bash
   # Should succeed - user accessing own data
   curl -H "Authorization: Bearer <valid-token>" \
        https://yourdomain.com/api/goals
   ```

2. **Test without authentication:**
   ```bash
   # Should fail - no auth token
   curl https://yourdomain.com/api/goals
   ```

3. **Check Firebase Console:**
   - Go to Firestore → Rules tab
   - Verify deployment timestamp

## Admin Setup

To grant admin privileges to a user:

```python
# backend/scripts/set_admin_claim.py
from firebase_admin import auth

def set_admin(uid):
    auth.set_custom_user_claims(uid, {'admin': True})
    print(f"Admin claim set for user: {uid}")

# Usage:
set_admin("user-uid-here")
```

## Troubleshooting

### Issue: "Permission denied" errors

**Solution:** Verify `user_id` field exists in documents:
```javascript
// All documents must have user_id field
{
  "user_id": "firebase-uid",
  "other": "data"
}
```

### Issue: Admin can't access feedback

**Solution:** Set custom claim via Firebase Admin SDK:
```bash
firebase auth:import admin_users.json --hash-algo=STANDARD_SCRYPT
```

## Security Notes

- Rules are deployed globally (affect all clients)
- Backend API still validates via middleware (`verify_token`)
- **Defense in depth:** Both Firestore Rules + Backend validation
- Rules update takes ~1 minute to propagate

## Related Files

- `/backend/auth_middleware.py` - Token verification
- `/backend/firestore_manager.py` - Database operations
- `/Docs/security_audit.md` - Full security audit

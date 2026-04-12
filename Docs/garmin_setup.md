# Garmin Credentials Setup Guide

This guide explains how to configure encrypted per-user Garmin credentials.

---

## Quick Setup (Local Development)

### Step 1: Generate Encryption Key

Run this command in your backend directory:

```bash
cd backend
../.venv/Scripts/python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

**Output example:**
```
ENCRYPTION_KEY=NT8pIUxrMs3lDaECrFkC262lg2tcMCFdAxihCE0gvJU=
```

### Step 2: Create `.env` File

Create `backend/.env` and add the generated key:

```bash
# backend/.env
GOOGLE_APPLICATION_CREDENTIALS=service_account_key.json
ENCRYPTION_KEY=NT8pIUxrMs3lDaECrFkC262lg2tcMCFdAxihCE0gvJU=
```

> [!CAUTION]
> **Never commit `.env` to Git!** The `.gitignore` should already exclude it.

### Step 3: Restart Backend

```bash
# If using Docker
docker-compose restart backend

# If running manually
cd backend
../.venv/Scripts/activate
uvicorn main:app --reload
```

---

## Verify Setup

### Test Encryption Helper

```bash
cd backend
../.venv/Scripts/python encryption_helper.py
```

**Expected output:**
```
Encryption Helper Self-Test

Original:  test_garmin_password_123
Encrypted: gAAAAABm...
Decrypted: test_garmin_password_123

Encryption/Decryption working correctly!
```

### Test API Endpoint

1. **Frontend:** Navigate to Profile page (`/profile`)
2. **Enter Garmin credentials:**
   - Email: `your.garmin.email@example.com`
   - Password: `your_garmin_password`
3. **Click "Connect Garmin"**

**Expected result:**
  - `password_encrypted`: Should be unreadable blob (e.g., `gAAAAABm...`)
  - Dashboard Banner: The "Connect Garmin" banner on the dashboard should disappear.

---

## Security Best Practices

### Do

1. **Generate unique key per environment:**
   - Development: One key
   - Production: Different key (stored in secret manager)

2. **Store key securely:**
   - Local: `.env` file (gitignored)
   - Production: Google Secret Manager, AWS Secrets Manager, etc.

3. **Backup encryption key:**
   - Without the key, encrypted data is **permanently unrecoverable**
   - Store key backup in secure password manager (1Password, Bitwarden)

### Don't

1. Never commit `ENCRYPTION_KEY` to Git
2. Never share the key via email/Slack
3. Never change the key once data is encrypted (old data becomes unreadable)

---

## Production Deployment

### Google Cloud Secret Manager (Recommended)

1. **Create Secret:**
   ```bash
   echo -n "your-encryption-key-here" | gcloud secrets create encryption-key --data-file=-
   ```

2. **Update Docker/Cloud Run:**
   ```yaml
   environment:
     - ENCRYPTION_KEY=${SECRET:encryption-key}
   ```

3. **Grant Access:**
   ```bash
   gcloud secrets add-iam-policy-binding encryption-key \
     --member="serviceAccount:your-service-account@project.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

---

## Testing

### Unit Test (Future TODO)

```python
# tests/test_encryption.py
def test_encryption_roundtrip():
    from encryption_helper import encrypt_text, decrypt_text
    
    original = "my_password_123"
    encrypted = encrypt_text(original)
    decrypted = decrypt_text(encrypted)
    
    assert decrypted == original
    assert encrypted != original  # Ensure it's actually encrypted
```

### Manual Test

1. **Save credentials via UI**
2. **Check Firestore:**
   - Password should be encrypted (unreadable)
3. **Fetch with API:**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8001/garmin/status
   ```
   **Expected:**
   ```json
   {
     "connected": true,
     "username": "your.email@example.com"
   }
   ```

---

## Troubleshooting

### Error: "ENCRYPTION_KEY not found"

**Cause:** Environment variable not set

**Solution:**
```bash
# Check if .env exists
ls backend/.env

# If missing, create it with:
echo "ENCRYPTION_KEY=your-key-here" > backend/.env
```

### Error: "Invalid token" when decrypting

**Cause:** Encryption key changed after data was encrypted

**Solution:**
- Restore original encryption key from backup
- OR delete all encrypted credentials and re-enter

### Error: "OAuth1 token is required for OAuth2 refresh"

**Cause:** `garth` library bug – token refresh fails after initial OAuth2 login.

**Solution (automatic):** The backend saves the OAuth2 token to Firestore after first sync. Subsequent syncs resume from the saved token. If the error persists, disconnect and reconnect your Garmin account in Profile settings to force a fresh token save.

---

### Docker: Encryption not working

**Cause:** `.env` not mounted to Docker container

**Solution:**
```yaml
# docker-compose.yml
services:
  backend:
    env_file:
      - backend/.env
```

---

## Firestore Schema

```
users/
  {uid}/
    garmin_credentials/
      default/
        - username: "user@example.com"        (plaintext – email is not sensitive)
        - password: "your_password"           (AES-256 encrypted)
        - garth_token_files_encrypted: "gAAAAABm..." (AES-256 encrypted OAuth1/2 tokens, added after first sync)
        - tokens_updated_at: timestamp
        - created_at: timestamp
        - last_updated: timestamp
```

---

## Related Documentation

- [authentication.md](authentication.md) – Firebase Auth implementation
- [Backend Encryption Helper](https://github.com/Samih/health_ai/blob/main/backend/encryption_helper.py)
- [Firestore Manager](https://github.com/Samih/health_ai/blob/main/backend/firestore_manager.py)

---

## OAuth2 Token Cache

After the first successful Garmin login, `fetch_garmin_data.py` saves the **garth OAuth2 token** to Firestore (encrypted). On subsequent syncs the token is loaded instead of performing a full re-login. This avoids the known `garth` library error:

> `OAuth1 token is required for OAuth2 refresh`

**Flow:**
1. First sync → full email/password login → token saved as `garth_tokens_encrypted`
2. Later syncs → token loaded → session resumed without re-login
3. If token expired or load fails → automatic fallback to fresh login

**Security:** Token is encrypted with the same AES-256 (Fernet) key as the password. It is never stored in plaintext.

---

**Last Updated:** 2026-03-04  
**Security Level:** AES-256 Encryption (Fernet)

---

## Exporting Workouts to Garmin

You can export AI-generated training plans directly to your Garmin Connect calendar.

### Prerequisites
1.  **Grant Permissions:** Ensure your Garmin account is connected in the **Profile/Settings** page.
2.  **Generate Plan:** Use the **AI Coach** to generate a training plan. Only AI-generated workouts contain the structured data needed for export.

### How to Export
1.  Navigate to the **Training Calendar**.
2.  Click on a **Planned Workout** (Blue card).
3.  In the workout details modal, click the **"Send to Garmin Device"** button.
4.  Wait for the success message ("Sent to Garmin").

### Syncing to Device
Once uploaded, open your **Garmin Connect App** on your phone or sync your watch via Wi-Fi/Bluetooth. The workout will appear in your device's training calendar for that day.

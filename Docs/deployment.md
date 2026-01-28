# Deployment Guide 🚀

## Environments

We support three standard environments:

### 1. Development (Local)
- **Use Case:** Local coding and testing.
- **Config:** `APP_ENV=development`
- **Features:**
  - Debug Mode: ON (Detailed stack traces)
  - CORS: Allows localhost
  - Reload: Hot reloading enabled
- **Command:**
  ```bash
  docker-compose up
  ```

### 2. Production
- **Use Case:** Live public usage.
- **Config:** `APP_ENV=production`
- **Features:**
  - Debug Mode: OFF (Generic error messages)
  - CORS: Strict (requires `FRONTEND_URL`)
  - Reload: Disabled
- **Command:**
  ```bash
  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
  ```

### 3. Staging (Optional)
- **Config:** `APP_ENV=staging`
- Mimics production but might use a test database.

## Configuration

Settings are managed in [`backend/config.py`](../backend/config.py).  
Hierarchy is handled by Pydantic: `Settings` -> `DevelopmentSettings` / `ProductionSettings`.

## Security Notes
- Ensure `.env` is **NEVER** committed to Git.
- In production, set `FRONTEND_URL` to your actual domain (e.g., `https://healthai.app`).

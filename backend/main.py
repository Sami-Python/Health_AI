"""
Health AI Coach API - Main Application
=======================================

This is the entry point for the Health AI Coach FastAPI application.
All endpoint logic has been moved to modular routers under `routers/`.

Routers:
    - routers/goals.py      → Goal CRUD & progress calculation
    - routers/workouts.py    → Workout management, upload, skip/reschedule
    - routers/ai.py          → AI insights, chat, plans, metrics, weekly summary
    - routers/garmin.py      → Garmin connect, 2FA, credentials, status
    - routers/admin.py       → Admin endpoints (users, feedback, security)
    - routers/system.py      → Data refresh, auto-sync
    - routers/user.py        → Profile, GDPR export/delete, FCM, feedback
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import firestore_manager as db_manager
from config import get_settings
from logger import setup_logging, logger

# Optional: Google Cloud Error Reporting
try:
    from google.cloud import error_reporting
except ImportError:
    error_reporting = None

# ─── Configuration ────────────────────────────────────────────────────────────

settings = get_settings()

# Initialize Structured Logging
setup_logging()

# Force Firebase initialization before any request
try:
    db_manager.get_db()
    logger.info("Firebase Admin forced initialization successful")
except Exception as e:
    logger.error(f"Failed to force-initialize Firebase: {e}")

# Initialize Google Cloud Error Reporting (Production Only)
error_reporting_client = None
if settings.APP_ENV == "production":
    if error_reporting:
        try:
            error_reporting_client = error_reporting.Client(service=settings.APP_NAME, version=settings.VERSION)
            logger.info("Google Cloud Error Reporting initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Error Reporting: {e}")
    else:
        logger.warning("google-cloud-error-reporting library not found")

# ─── Rate Limiter ─────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Health AI Coach API",
    version=settings.VERSION,
    description="""
🏃 **Health AI Coach** - Your personal AI-powered endurance training assistant.

## Features

* **Goal Management**: Create, track, and manage training goals
* **AI Insights**: Get personalized training recommendations powered by Gemini
* **Garmin Integration**: Securely connect and sync Garmin data
* **Training Calendar**: Plan and track workouts
* **Analytics**: Visualize recovery metrics and training load

## Authentication

All endpoints (except `/health`) require Firebase Authentication.
Include the ID token in the `Authorization` header:

```
Authorization: Bearer <your-firebase-id-token>
```
""",
    contact={
        "name": "Health AI Support",
        "url": "https://github.com/Sami-Python/Health_AI",
    },
    license_info={
        "name": "MIT",
    },
)

# ─── Middleware ────────────────────────────────────────────────────────────────

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Structured logging for every incoming HTTP request."""
    import time
    start_time = time.time()

    logger.info(f"📥 [REQUEST] {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000

    logger.info(
        "Request processed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time, 2),
            "ip": request.client.host if request.client else "unknown"
        }
    )

    return response


# ─── Rate Limiting ────────────────────────────────────────────────────────────

app.state.limiter = limiter


async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Logs the rate limit violation before returning the standard response."""
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        "Rate limit exceeded",
        extra={
            "event": "security_rate_limit",
            "ip": client_ip,
            "path": request.url.path,
            "limit": str(exc)
        }
    )

    # Persist to Firestore for Admin Dashboard
    try:
        db_manager.log_security_event("rate_limit_exceeded", {
            "ip": client_ip,
            "path": request.url.path,
            "limit": str(exc),
            "user_agent": request.headers.get("user-agent", "unknown")
        })
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")

    return _rate_limit_exceeded_handler(request, exc)


app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# ─── Monitoring ───────────────────────────────────────────────────────────────

from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# ─── Global Error Handling ────────────────────────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    logger.error(f"CRITICAL ERROR ({settings.APP_ENV}): {exc}", extra={"path": request.url.path})

    # Report to Google Cloud Error Reporting (Production only)
    if error_reporting_client:
        try:
            error_reporting_client.report_exception()
        except Exception as er_err:
            logger.error(f"Failed to report to Cloud Error Reporting: {er_err}")

    # Return generic message in production
    if not settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "correlation_id": "contact-support"}
        )

    # In development (debug=True), return detailed error
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )


# ─── Root Endpoints ───────────────────────────────────────────────────────────

@app.get("/", tags=["System"], summary="Root Endpoint")
def read_root(request: Request):
    return {"message": "Health AI API is running! (Firestore Version)"}


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}


# ─── Register Routers ─────────────────────────────────────────────────────────

from routers.goals import router as goals_router
from routers.workouts import router as workouts_router
from routers.ai import router as ai_router
from routers.garmin import router as garmin_router
from routers.admin import router as admin_router
from routers.system import router as system_router
from routers.user import router as user_router

app.include_router(goals_router)
app.include_router(workouts_router)
app.include_router(ai_router)
app.include_router(garmin_router)
app.include_router(admin_router)
app.include_router(system_router)
app.include_router(user_router)

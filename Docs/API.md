# Health AI Coach API Documentation

**Base URL:** `http://localhost:8000` (development)  
**Production:** `https://health-ai-backend-35976089058.europe-north1.run.app`  
**API Docs:** `https://health-ai-backend-35976089058.europe-north1.run.app/docs` (Swagger UI)  
**Version:** 1.2.0


---

## Authentication

All endpoints require Firebase Authentication (except `/health`).

**Header:**
```
Authorization: Bearer <firebase-id-token>
```

**Getting a token** (from frontend):
```typescript
const token = await user.getIdToken();
```

---

## API Endpoints

### Goals Management

#### `GET /goals`
Get all active goals for authenticated user.

**Tags:** Goals  
**Rate Limit:** 20/min  
**Response:**
```json
[
  {
    "id": "goal123",
    "activity_type": "Running",
    "target_value": 30,
    "target_unit": "km",
    "period_type": "weekly",
    "status": "ACTIVE",
    "progress": 65.5
  }
]
```

---

#### `POST /goals`
Create a new training goal.

**Tags:** Goals  
**Rate Limit:** 20/min  
**Request Body:**
```json
{
  "activity_type": "Running",
  "target_value": 50,
  "target_unit": "km",
  "period_type": "weekly",
  "frequency": "Weekly",
  "description": "Marathon prep"
}
```

**Response:** `201 Created`

---

#### `PUT /goals/{goal_id}`
Update an existing goal.

**Tags:** Goals  
**Rate Limit:** 20/min

---

#### `DELETE /goals/{goal_id}`
Delete a goal.

**Tags:** Goals  
**Rate Limit:** 20/min  
**Response:** `204 No Content`

---

### Workouts

#### `GET /workouts/next`
Get the next recommended workout.

**Tags:** Workouts  
**Rate Limit:** 20/min  
**Response:**
```json
{
  "activity_type": "Running",
  "duration_min": 45,
  "intensity": "Easy",
  "description": "Recovery run at Zone 2"
}
```

---

#### `POST /workouts/log`
Log a manual workout.

**Tags:** Workouts  
**Rate Limit:** 20/min  
**Request Body:**
```json
{
  "date": "2024-01-15",
  "activity_type": "Running",
  "duration_min": 60,
  "distance_km": 10.5,
  "notes": "Felt great!"
}
```

---

#### `GET /workouts/history`
Get past completed workouts (status=DONE), ordered by date descending.

**Tags:** Workouts  
**Rate Limit:** 20/min  
**Parameters:**
- `limit` (optional): Max items (default 50)

**Response:**
```json
[
  {
    "date": "2024-01-15",
    "activity": "Running",
    "duration_min": 45,
    "status": "DONE",
    "source": "GARMIN"
  }
]
```

---

#### `GET /workouts/upcoming`
Get all future planned (PENDING) workouts.

**Tags:** Workouts  
**Rate Limit:** 20/min

---

#### `POST /workouts/manual`
Log a manual workout.

**Tags:** Workouts  
**Request Body:**
```json
{
  "date": "2024-01-15",
  "activity": "Running",
  "duration_min": 60,
  "rpe": 7,
  "notes": "Easy run"
}
```

---

---

#### `POST /workouts/upload`
Upload a structured workout to Garmin Connect.

**Tags:** Workouts  
**Rate Limit:** 5/min  
**Request Body:**
```json
{
  "workout": { "...Garmin workout JSON..." },
  "date": "2024-01-20"
}
```

---

#### `POST /workouts/{workout_id}/skip`
Skip a workout and trigger AI rescheduling.

**Tags:** Workouts, AI  
**Rate Limit:** 5/min  
**Response:**
```json
{
  "new_date": "2024-01-22",
  "reasoning": "Based on your current body battery...",
  "push_message": "Treeni rästissä? 🏃 Tehdään se maanantaina!"
}
```

---

#### `PATCH /workouts/{workout_id}`
Change a workout's date (reschedule).

**Tags:** Workouts  
**Rate Limit:** 10/min

---

#### `DELETE /workouts/{workout_id}`
Delete a workout.

**Tags:** Workouts  
**Rate Limit:** 10/min  
**Response:** `200 OK`


#### `GET /workouts/weekly-status`
Get weekly training status summary.

**Tags:** Workouts, Analytics  
**Rate Limit:** 20/min  
**Response:**
```json
{
  "current_load": 540,
  "planned_load": 600,
  "load_percentage": 90,
  "workouts_completed": 4,
  "workouts_planned": 5
}
```

---

#### `GET /gamification/summary`
Get user gamification metrics and execution score summary.

**Tags:** Gamification, Workouts  
**Rate Limit:** 20/min  
**Response:**
```json
{
  "average_score": 85.5,
  "workouts_analyzed": 10,
  "streak_days": 5,
  "level": 3
}
```

---

### AI & Insights

#### `GET /ai/insight`
Get daily AI-powered training insight.

**Tags:** AI  
**Rate Limit:** 10/min  
**Caching:** 24 hours (per user)  
**Response:**
```json
{
  "insight": "Your recovery is excellent today. Consider a moderate intensity run...",
  "cached": true,
  "generated_at": "2024-01-15T08:00:00Z"
}
```

---

#### `POST /plans/generate`
Generate a training plan with AI (N days ahead).

**Tags:** AI  
**Rate Limit:** 5/min  
**Daily Limit:** 5 generations  
**Request Body:**
```json
{
  "days": 7,
  "rejected_plan_details": null
}
```

---

#### `GET /plans/history`
Get recent AI-generated training plans.

**Tags:** AI  
**Parameters:**
- `limit` (optional): Max items (default 5)

---


### Analytics

#### `GET /metrics/history`
Get historical recovery metrics (last 90 days).

**Tags:** Analytics  
**Rate Limit:** 20/min  
**Response:**
```json
[
  {
    "date": "2024-01-15",
    "sleep_score": 85,
    "body_battery": 78,
    "hrv": 65,
    "training_load": 120
  }
]
```

---

#### `GET /readiness`
Get latest readiness/body battery score.

**Tags:** Analytics  
**Rate Limit:** 20/min  
**Response:**
```json
{
  "readiness": "85",
  "date": "2024-01-15"
}
```

---

#### `GET /ai/model-metrics`
Get current AI model performance metrics.

**Tags:** Analytics  
**Rate Limit:** 20/min  
**Response:**
```json
{
  "mae": 3.42,
  "r2": 0.85,
  "last_trained": "2024-01-15",
  "top_features": {
    "totalSleep_minutes": 0.35,
    "averageStressLevel": 0.25,
    "totalSteps": 0.15
  },
  "data_points": 1450
}
```

---

### User Profile

#### `GET /profile`
Get user profile data.

**Tags:** User  
**Rate Limit:** 20/min  
**Response:**
```json
{
  "age": 35,
  "weight": 75.0,
  "height": 180,
  "gender": "male"
}
```

---

#### `PUT /profile`
Update user profile.

**Tags:** User  
**Rate Limit:** 20/min  
**Request Body:**
```json
{
  "age": 35,
  "weight": 75.0,
  "height": 180,
  "gender": "male",
  "resting_heart_rate": 60,
  "max_heart_rate": 190
}
```

---

#### `POST /notifications/token`
Register an FCM token for push notifications.

**Tags:** Notifications  
**Rate Limit:** 5/min
```json
{
  "token": "fcm-token-here"
}
```

---

#### `GET /user/export`
Export all user data (GDPR compliance).

**Tags:** User, GDPR  
**Rate Limit:** 3/hour  
**Response:** JSON with all user data (goals, workouts, profile, metrics)

---

#### `DELETE /account`
Delete user account and all associated data (GDPR Right to Erasure).

**Tags:** User, GDPR  
**Rate Limit:** 1/hour  
**Response:** `200 OK`

> ⚠️ **Irreversible.** Deletes: Firestore data, Firebase Auth user, Garmin credentials, metrics.


---

### Garmin Integration

#### `POST /garmin/credentials`
Save encrypted Garmin credentials.

**Tags:** Garmin  
**Rate Limit:** 5/hour  
**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Security:** Password encrypted with AES-256 before storage.

---

#### `POST /garmin/test`
Test Garmin credentials without saving them.

**Tags:** Garmin  
**Rate Limit:** 5/hour  
**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:** `200 OK` (if credentials are correct)

---

#### `GET /garmin/status`
Check Garmin connection status.

**Tags:** Garmin  
**Rate Limit:** 20/min  
**Response:**
```json
{
  "connected": true,
  "username": "your_username"
}
```

---

#### `POST /garmin/connect`
Initiate Garmin login with MFA support.

**Tags:** Garmin  
**Rate Limit:** 5/min
**Response (MFA required):**
```json
{
  "status": "mfa_required",
  "session_id": "uuid-here"
}
```

---

#### `POST /garmin/connect/mfa`
Complete Garmin login with MFA code.

**Tags:** Garmin  
**Rate Limit:** 10/min
**Request Body:**
```json
{
  "session_id": "uuid-here",
  "mfa_code": "123456"
}
```

---

#### `DELETE /garmin/credentials`
Disconnect Garmin account.

**Tags:** Garmin  
**Rate Limit:** 5/hour

---

### System

#### `POST /system/refresh`
Triggers Garmin data fetch and model retraining asynchronously via BackgroundTasks.

**Tags:** System  
**Query Parameters:**
- `mode` (string, optional): Training mode. Accepts `incremental` (Quick Sync, 1-day API overlap, no grid search) or `full` (Full Retrain, 360-day fallback or 5-day overlap, full grid search). Defaults to `incremental`.

**Rate Limit:** 2/hour  
**Response:**
```json
{
  "status": "success",
  "message": "Refresh task started in background."
}
```

---

#### `GET /system/refresh/status`
Returns the current status of the background refresh task.

**Tags:** System  
**Rate Limit:** No limit  
**Response:**
```json
{
  "status": "in_progress",
  "progress": 30,
  "message": "Fetching Garmin Data...",
  "error": null
}
```

---

#### `POST /feedback`
Submit user feedback.

**Tags:** System  
**Rate Limit:** 10/hour  
**Request Body:**
```json
{
  "category": "bug",
  "message": "Dashboard not loading",
  "severity": "medium"
}
```

---

#### `GET /admin/feedback`
Get all user feedback (Admin only).

**Tags:** System, Admin  
**Rate Limit:** 20/min  
**Parameters:**
- `status` (optional): Filter by status (NEW, READ, ARCHIVED)
- `category` (optional): Filter by category
- `limit` (optional): Max items (default 100)

**Security:** Requires Admin email (verified via `verify_admin`).

**Response:**
```json
{
  "total": 5,
  "feedback": [
    {
      "category": "bug",
      "message": "Dashboard error",
      "user_id": "uid123",
      "timestamp": "2024-01-15T12:00:00Z"
    }
  ]
}
```


---

#### `GET /admin/security-events`
Get security logs (rate limit hits, auth failures).

**Tags:** System, Admin  
**Rate Limit:** 50/min  
**Parameters:**
- `limit` (optional): Max items (default 100)
- `type` (optional): Filter by event type (e.g., `rate_limit_exceeded`)

**Security:** Requires Admin email.

**Response:**
```json
{
  "total": 5,
  "events": [
    {
      "type": "rate_limit_exceeded",
      "ip": "1.2.3.4",
      "limit": "5 per minute",
      "timestamp": "2024-01-15T12:05:00Z"
    }
  ]
}
```

---

#### `POST /admin/revoke-tokens/{uid}`
Force logout a user by revoking their refresh tokens.

**Tags:** System, Admin  
**Rate Limit:** 5/min  
**Parameters:**
- `uid` (path): User UID to logout

**Security:** Requires Admin email.

**Response:**
```json
{
  "status": "success",
  "message": "Tokens revoked for uid123"
}
```

---

#### `GET /admin/users`
List all registered users (Firebase Auth).

**Tags:** System, Admin  
**Rate Limit:** 20/min  
**Security:** Requires Admin email.

**Response:**
```json
{
  "users": [
    {
      "uid": "user123",
      "email": "user@example.com",
      "display_name": "John Doe",
      "disabled": false,
      "metadata": {
        "last_sign_in": 1700000000000,
        "creation_time": 1690000000000
      }
    }
  ],
  "total": 50
}
```

---

### AI Chat

#### `POST /ai/chat`
Interactive chat with the AI Health Coach.

**Tags:** AI  
**Rate Limit:** 10/min  
**Request Body:**
```json
{
  "message": "How was my sleep last night?",
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "model", "content": "Hi! How can I help?"}
  ]
}
```

**Response:**
```json
{
  "reply": "Your sleep was excellent! You got 8 hours...",
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "model", "content": "Hi! How can I help?"},
    {"role": "user", "content": "How was my sleep last night?"},
    {"role": "model", "content": "Your sleep was excellent!..."}
  ]
}
```




#### `GET /health`
Health check endpoint (no auth required).

**Tags:** System  
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

---

## Response Models

### Common Fields

All resources include:
- `created_at`: ISO 8601 timestamp
- `updated_at`: ISO 8601 timestamp (if applicable)
- `user_id`: Firebase UID (internal, not returned to client)

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input: target_value must be positive"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Goal not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

### 500 Internal Server Error
```json
{
  "detail": "An unexpected error occurred"
}
```

---

## Rate Limits

| Category | Limit |
|----------|-------|
| Standard endpoints | 20 requests/minute |
| AI endpoints | 10 requests/minute |
| Data refresh | 2 requests/hour |
| Garmin credentials | 20 requests/hour |
| User data export | 3 requests/hour |
| Account deletion | 1 request/hour |

---

## Testing

### Using Swagger UI

1. Navigate to `http://localhost:8001/docs`
2. Click "Authorize" button
3. Enter your Firebase ID token: `Bearer <token>`
4. Try endpoints interactively

### Using cURL

```bash
# Get goals
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8001/goals

# Create goal
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"activity_type":"Running","target_value":50,"target_unit":"km","period_type":"weekly"}' \
  http://localhost:8001/goals
```

### Using Postman

Import collection: `docs/postman_collection.json` (TODO)

---

## Related Documentation

- [Authentication](authentication.md) – Firebase Auth setup
- [Garmin Setup](garmin_setup.md) – Garmin credentials encryption
- [Architecture](arkkitehtuuri.md) – System architecture
- [Mobile App](../mobile/README.md) – Flutter mobile app

---

**Last Updated:** 2026-03-16  
**Maintained by:** Health AI Team

# Vaatimusmäärittely - Health AI Coach

**Versio:** 1.0  
**Status:** Production Ready  
**API:** v1.0.0

---

## 📋 Projektin Kuvaus

Dataohjautuva valmennusjärjestelmä, joka yhdistää:
- **Garmin-data** (Body Battery, uni, stressi, treenit)
- **XGBoost ML-malli** (vireystilan ennustus)
- **Google Gemini AI** (personoidut treenisuositukset)

**Tech Stack:**
- Frontend: Next.js 14 + TypeScript + Tailwind
- Backend: Python 3.12 + FastAPI
- Database: Firebase Firestore
- AI: Google Gemini 2.5 Flash
- ML: XGBoost + MLflow

---

## 🎯 Keskeiset Ominaisuudet

### 1. Authentication
- Google OAuth (Firebase Auth)
- Token-based API (Bearer JWT)
- Multi-user data isolation (`user_id` filtering)

### 2. Dashboard
- **Palautumismetriikat:** Body Battery, Sleep, Stress, HRV
- **AI Daily Insight:** 24h cache, Gemini 2.5 Flash
- **Kuvaajat:**
  - Recovery Chart (BB + Sleep, 30 pv)
  - Load Chart (Daily load, 14 pv)
  - Performance Chart (CTL/ATL/TSB, 90 pv)

### 3. Goals Management (CRUD)
- **Tyypit:** Weekly / Monthly / Race
- **Kentät:** Activity, Target Value, Unit, Period, Date (Race)
- **Progress:** Auto-calculate from workouts
- **Race Goals:** Countdown timer ("X weeks to go")

### 4. Training Calendar
- Kuukausinäkymä (completed + planned workouts)
- Drag & drop suunnitelmien siirtämiseen
- Trash can → AI regenerates replacement workout

### 5. AI Coach
- **Daily Insight:** Body Battery interpretation + training advice
- **Weekly Plan:** 7 workout schedule (type, duration, intensity)
- **Rate Limits:** 10/min (insight), 5/hour (plan)

### 6. Garmin Integration
- **Encrypted Credentials:** AES-256 (Fernet)
- **Storage:** `users/{uid}/garmin_credentials/default`
- **Sync:** POST `/system/refresh` (2/hour limit)
- **Data:** Dual-write (CSV cache + Firestore)

### 7. User Profile & GDPR
- Profile fields: Age, Weight, Height, Gender, HR zones
- **Data Export:** JSON download (GET `/user/export`)
- **Account Deletion:** Full wipe (DELETE `/user/account`)
- **Feedback Form:** Internal support system

### 8. Admin Dashboard
- View user feedback (GET `/admin/feedback`)
- Filter by status/category
- Admin-only email check

---

## ⚙️ Tekniset Vaatimukset

### Performance
- API response: 95% < 500ms (AI: < 3s)
- Frontend load: < 2s Dashboard
- Concurrent users: 100+

### Security
- ✅ Firebase Auth on all endpoints (except `/health`)
- ✅ AES-256 encryption (Garmin passwords)
- ✅ HTTPS (production)
- ✅ Rate limiting (SlowAPI)
- ✅ Row-level security (Firestore `user_id` filters)

### Scalability
- Stateless backend (horizontal scaling ready)
- Firestore: 10,000+ users support
- Indexes: Optimized for `user_id` queries

### Quality
- **Testing:** pytest (backend), Jest (frontend)
- **Linting:** Ruff (Python), ESLint (TS)
- **CI/CD:** GitHub Actions (tests + docs deploy)

---

## 🔌 API Endpoints (Tärkeimmät)

| Endpoint | Method | Auth | Rate | Kuvaus |
|----------|--------|------|------|--------|
| `/health` | GET | ❌ | - | Health check |
| `/goals` | GET/POST/PUT/DELETE | ✅ | 20/min | Goals CRUD |
| `/workouts/log` | POST | ✅ | 20/min | Manual workout |
| `/ai/insight` | GET | ✅ | 10/min | Daily AI insight (cached 24h) |
| `/ai/generate-plan` | POST | ✅ | 5/hour | Weekly plan |
| `/user/export` | GET | ✅ | 3/hour | GDPR data export |
| `/user/account` | DELETE | ✅ | 1/hour | Delete account |
| `/garmin/credentials` | POST/DELETE | ✅ | 5/hour | Save/remove Garmin login |
| `/system/refresh` | POST | ✅ | 2/hour | Fetch Garmin data |
| `/admin/feedback` | GET | ✅ (Admin) | 20/min | View feedback |

**Swagger UI:** `http://localhost:8001/docs`

---

## 🗄️ Firestore Schema

```
firestore/
├── users/{uid}
│   ├── profile (doc)
│   ├── garmin_credentials/default (subcol)
│   └── daily_insights/{date} (subcol)
├── goals/ (col, indexed by user_id)
├── workouts/ (col, indexed by user_id)
├── plans/ (col, indexed by user_id)
├── feedback/ (col)
└── garmin_metrics/{user_id}/daily_metrics/{date}
```

**Security Rules:** `user_id == request.auth.uid` (row-level isolation)

---

## 🔐 Environment Variables

### Backend (`.env`)
```bash
APP_ENV=development|production
GOOGLE_APPLICATION_CREDENTIALS=backend/service_account_key.json
ENCRYPTION_KEY=<base64-fernet-key>
FRONTEND_URL=http://localhost:3000
GEMINI_API_KEY=<your-key>
```

### Frontend (`frontend/.env.local`)
```bash
NEXT_PUBLIC_FIREBASE_API_KEY=<your-key>
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=<project>.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=<project-id>
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## 🚀 Deployment

### Local Dev
```bash
# Backend
cd backend
uvicorn main:app --reload --port 8001

# Frontend
cd frontend
npm run dev
```

### Docker
```bash
docker-compose up backend
```

### Production
- **Frontend Hosting:** Vercel / Firebase Hosting
- **Backend:** Cloud Run / VPS (Docker)
- **Database:** Firebase Firestore (managed)
- **Secrets:** Google Secret Manager

---

## 🛡️ GDPR & Security

### Data Protection
- ✅ Garmin passwords encrypted (AES-256)
- ✅ User data isolation (Firestore rules + backend filters)
- ✅ Data export endpoint (JSON)
- ✅ Account deletion (full wipe)

### Security Best Practices
- HTTPS only (production)
- No secrets in code (`.gitignore`)
- Rate limiting on all endpoints
- Error messages sanitized (production)
- Token validation on every request

---

## ⚠️ Known Limitations

1. **Garmin API:** Unofficial (`garth` library) - may break with updates
2. **AI Costs:** Scales with users (~$0.01/user/month)
3. **Offline Mode:** Not supported (requires internet)
4. **Browser Support:** No IE11 (Next.js requires ES6+)
5. **CSV Legacy:** Historical Garmin data still in CSV (95% migrated to Firestore)

---

## 📊 MLOps (MLflow)

- **Experiment:** `xgboost_readiness_prediction`
- **Database:** `backend/data/mlflow.db` (SQLite)
- **Logged:** Parameters, Metrics (R², MAE, RMSE), Feature importance
- **UI:** `mlflow ui --backend-store-uri sqlite:///backend/data/mlflow.db`

---

## 🔗 Related Docs

- [API.md](API.md) - Full API reference
- [arkkitehtuuri.md](arkkitehtuuri.md) - System architecture
- [authentication.md](authentication.md) - Firebase Auth implementation
- [production_roadmap.md](production_roadmap.md) - Scaling plan (0 → 10K users)
- [garmin_setup.md](garmin_setup.md) - Garmin credentials setup

---

**Live Landing Page:** https://personal-ai-coach-92c39.web.app  
**Status:** ✅ Production Ready  
**Last Updated:** 2026-01-29

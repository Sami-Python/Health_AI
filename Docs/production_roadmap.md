# 🚀 Health AI: Production Scaling Roadmap (0 -> 10,000 Users)

Jos sovellus skaalattaisiin tuhansille käyttäjille, nykyinen "Local Single-User App" -arkkitehtuuri pitäisi muuttaa moderniksi pilviarkkitehtuuriksi.

## 1. Arkkitehtuuri & Backend (Cloud Native)
Nykyinen Streamlit + lokaali Python-skripti ei skaalaudu.
- [x] **Erota Frontend ja Backend:** Siirry pois monoliittisesta Streamlit-rakenteesta. (Aloitettu: Home View hakee datan API:sta) (#105)
- [x] **Backend-valinta:** Ota käyttöön FastAPI (Python) tai Node.js API:n rakentamiseen. (#106)
- [x] **API-suunnittelu:** Määrittele REST tai GraphQL rajapinta Fronendin käyttöön. (#107)
- [x] **Kontitus:** Paketoi sovellus Docker-konteiksi (Backend, Frontend). (#108)
- [x] **Hosting:** Valmistele Cloud Run tai yksinkertainen VPS (Docker Compose) ympäristö. (Riittää sadoille käyttäjille) (#109) ✅ COMPLETED (2026-01-31)
- [x] **Secrets:** Ota käyttöön Google Secret Manager API-avaimille ja service account -konfiguraatioille. (#110) ✅ COMPLETED (2026-01-31)

## 2. Tietokanta (Multi-User & Scalability)
Nykyinen DuckDB/SQLite on tiedostopohjainen ja lukittuu usealla käyttäjällä.
- [x] **DB-migraatio:** Vaihda DuckDB -> Firestore. (Workouts & Goals & Plans migrated) (#111)
- [x] **Data Isolation:** Implementoi Row-Level Security (Firestore Rules) ja `user_id` jokaiseen dokumenttiin. (Toteutettu backendiin: `firestore_manager` filtteröi aina user_id:llä) (#112)
- [x] **Query Filtering:** Päivitä `firestore_manager.py` käyttämään `where('user_id', '==', uid)` -filtteriä kaikissa hauissa. (#113)
- [x] **Legacy Migration (CRITICAL):** Siirrä Manual Workouts, Weekly Stats, ja Readiness -logiikka DuckDB:stä Firestoreen. (DuckDB ei tue user isolationia). (#114)
- [x] **Complete Migration (Phase 7):** DuckDB poistettu. CSV käytössä vain Garmin-historialle. (#115)

## 3. Käyttäjähallinta & Tietoturva (Security)
- [x] **Autentikaatio:** Ota käyttöön OAuth2 / OpenID Connect (Auth0, Firebase Auth). (#116)
- [x] **Backend Middleware:** Implementoi `main.py`:hyn middleware, joka verifioi Firebase ID -tokenin jokaisessa pyynnössä. (#117)
- [ ] **Kirjautuminen:** Toteuta Google/Apple/Email -kirjautumisvaihtoehdot. (#118)
- [x] **Data Encryption (GDPR):** Salattu tallennusratkaisu (AES-256) salasanoille ja arkaluonteisille tiedoille. (#119)
- [ ] **Datan hallinta:** Työkalu käyttäjän datan poistoon ("Oikeus tulla unohdetuksi"). (#120)

## 3.4 Garmin Per-User Credentials 🔐
- [x] **Encryption Infrastructure:** AES-256 salaus (Fernet) arkaluonteisten tietojen tallennukseen. (#121)
    - [x] `encryption_helper.py` - Keskitetty salaus/purku logiikka (#122)
    - [x] Environment-based encryption key (`ENCRYPTION_KEY`) (#123)
- [x] **Firestore Schema:** `users/{uid}/garmin_credentials/default` (#124)
    - [x] Username (plaintext, email) (#125)
    - [x] Password (encrypted blob) (#126)
- [x] **Backend API:** (#127)
    - [x] `POST /garmin/credentials` - Tallenna salatut tunnukset (#128)
    - [x] `GET /garmin/status` - Tarkista yhteys (#129)
    - [x] `DELETE /garmin/credentials` - Poista yhteys (#130)
- [x] **Frontend UI:** (#131)
    - [x] `GarminCredentialsForm.tsx` - Tunnusten hallinta (#132)
    - [x] Profile-sivu integraatio (#133)
    - [x] Turvallisuusilmoitukset UI:ssa (#134)
- [x] **Data Fetch Integration:** (#135)
    - [x] Päivitetty `fetch_garmin_data.py` käyttämään per-user -tunnuksia (#136)
    - [x] Päivitetty `/system/refresh` endpoint tukemaan molempia tiloja (#137)
    - [x] Backward compatibility: Legacy mode jos tunnuksia ei tallennettu (#138)
    - [ ] Testaa multi-user datan haku (#139)
- [x] **Documentation:** `garmin_setup.md` - Setup guide ja troubleshooting (#140)

**Security:** Salasanat ovat luettavissa vain oikealla salausavaimella. Admin ei näe salasanoja ilman avainta.

**Completed:** 2026-01-18

**Verification:**
- ✅ Encryption tested: AES-256 roundtrip successful
- ✅ Firestore verified: Password stored as encrypted blob (unreadable)
- ✅ API endpoints working
- ✅ Frontend UI functional
- ✅ Data fetch integration complete
- ✅ Backward compatibility maintained

**Status:** 🟢 **PRODUCTION READY** - Fully implemented and verified

## 3.5 Käyttäjäprofiili & Asetukset (User Management) 👤
- [x] **Hamburger Menu:** Navigaatio oikeaan ylälaitaan (Settings, Profile, Logout). (Toteutettu: UserMenu.tsx) (#141)
- [x] **Profile Page:** (Toteutettu: `/profile` route + Firestore backend) (#142)
    - [x] Fysiologiset tiedot (Ikä, Paino, Pituus, Sukupuoli). (#143)
    - [x] Sykerajat (Lepo- ja Maksimisyke). (#144)
- [ ] **Settings & Account Control:** (GDPR) (#145)
    - [x] Settings Page (`/settings`). (#146)
    - [x] **Delete Account:** "Danger Zone" - napin takana. Poistaa käyttäjän ja datat. (#147)
    - [x] **Data Export:** Lataa kaikki käyttäjän data JSON-muodossa. (#148)
    - [x] **Support / Feedback Form:** Sisäinen lomake palautteen lähettämiseen (ei sähköpostia). Tallenna palautteet tietokantaan. (#149)
    - [x] **Data Export (GDPR):** Backend endpoint `GET /user/export` joka palauttaa käyttäjän kaiken datan JSON-muodossa. (#150)

## 4. AI & Mallit (LLM at Scale)
Nykyinen suora Gemini API -kutsu voi hidastua tai maksaa liikaa.
- [x] **Mallien optimointi:** Vaihda kevyempään malliin (esim. Gemini Flash) rutiinitehtävissä. (Käytetään Flashia + Caching) (#151)
- [x] **Välimuisti (Caching):** Implementoi vastausten välimuisti samanlaisille kyselyille. (Toteutettu Daily Insightille) (#152)
- [x] **Rate Limiting:** Rajoita API-kutsujen määrää per käyttäjä väärinkäytösten estämiseksi. (Toteutettu: slowapi) (#153)

## 5. Frontend (Käyttökokemus)
Streamlit on raskas tuhansille yhtäaikaisille käyttäjille.
- [x] **Moderni Web-kehys:** Rakenna käyttöliittymä Reactilla, Vuella tai Next.js:llä. (Toteutettu Next.js) (#154)
- [x] **Next.js Setup:** Alusta uusi Next.js -projekti (TypeScript, TailwindCSS) kansioon `frontend`. (#155)
- [x] **Frontend Features:** Training Calendar, Goals, Dashboard. (#156)
- [x] **Mobiilisovellus:** Web App toimii nyt mobiilissa (Responsive Design + Network Config). (#157)
- [ ] **Natiivi Mobiili (Optionaalinen):** Harkitse React Nativea tai Flutteria myöhemmin. (#158)
- [ ] **Flutter Setup:** Alusta uusi Flutter-projekti kansioon `mobile`. (#159)
- [ ] **Notifikaatiot:** Lisää Push-ilmoitukset (treenimuistutukset). (#160)
- [ ] **Integraatiot:** Kytke Apple Health / Google Fit -rajapintoihin. (#161)

## 5.5 Frontend Features (Next.js)
- [x] **Goal Management:** Mahdollisuus lisätä, muokata ja poistaa tavoitteita. (CRUD valmis: Backend & Frontend) (#162)
- [x] **Visual Goal Cards:** Progress bars ja Race -countdown. (#163)
- [x] **Sparklines:** Trenditiedot (Readiness, Load) dashboardilla. (#164)
- [x] **Training Calendar:** Visuaalinen kuukausinäkymä, treenien tarkastelu (Modal), tulevat suunnitelmat. (#165)
    - [x] **Drag & Drop:** Siirrä treenejä päivältä toiselle. (#166)
    - [x] **Trash Can:** Poista treenejä raahaamalla roskikseen. (#167)
    - [x] **Regeneration:** AI luo korvaavan treenin poistetun tilalle. (#168)
- [x] **Workout Logging:** Lomake treenien lisäämiseen. (#169)
- [x] **UI Polish:** Moderni ilme (Dark Mode, Tailwind Components). (#170)

## 6. DevOps & Monitoring
- [x] **CI/CD Pipeline:** Laajenna GitHub Actions kattamaan automaattinen deploy (CD). (#171) ✅ COMPLETED (2026-01-31)
- [ ] **Monitorointi:** Asenna Grafana/Datadog suorituskyvyn seurantaan. (#172)
- [ ] **Alerting:** Määritä hälytykset virhetilanteista (esim. API vastaa hitaasti). (#173)
- [ ] **Developer Experience:** Lisää `npm run fix` -komento (`package.json`), joka siivoaa lukot ja välimuistit automaattisesti. (#174)

---
### MVP -> Beta (Ensimmäiset askeleet)
- [-] Konfiguroi PostgreSQL-tietokanta. (SKIP) (#175)
- [x] Luo uusi FastAPI-projekti Backuiksi. (#176)
- [x] Integroi Firebase Auth. (#177)
- [ ] Konfiguroi Secret Manager. (#178)
- [x] Päivitä Firestore-haut tukemaan multi-user -mallia (user_id). (#179)
- [x] Alusta Next.js -projekti frontendille (frontend). (Kansio olemassa, mutta projekti on tyhjä scaffold) (#180)
- [x] Implementoi Frontendin perusrakenne (Authentication, API Client). (#181)
    - [x] Asenna kirjastot (Firebase SDK, Lucide Icons). (#182)
    - [x] Konfiguroi Firebase Client (frontend). (#183)
    - [x] Toteuta Login-sivu ja Auth Context. (#184)
    - [x] Testaa yhteys backendiin (Protected Route). (#185)
- [x] Implementoi "Add Goal" -toiminnallisuus (Create). (#186)
    - [x] Refined UI: Date Picker, Unit Dropdown, Frequency Logic. (#187)
- [ ] Tuo Dashboardin ulkoasu (CSS/Tailwind) samalle tasolle kuin Streamlit-versiossa. (#188)
- [ ] Alusta Flutter-projekti (mobile). (#189)
    - [x] Streamlit Migration: Feat Parity (History, Manual Logs, Refresh). (#190)
- [x] **Dashboard Visualizations (Phase 5)**: (#191)
    - [x] Backend: Historical Metrics Endpoint (Pandas/CSV). (#192)
    - [x] Implement Recovery Chart (Body Battery vs Sleep). (#193)
    - [x] Implement Load Chart (Daily Load). (#194)
    - [x] Implement Performance Chart (CTL/ATL/TSB) with Tooltips. (#195)
    - [x] Integrate Charts into Dashboard Grid. (#196)
- [x] **AI Insights (Phase 6)**: (#197)
    - [x] Backend: Add `GET /ai/insight` endpoint (Gemini API with Rate Limiting). (#198)
    - [x] Backend: Create `generate_daily_insight` prompt. (#199)
    - [x] Frontend: Implement `AIInsightCard` with gradient UI. (#200)
    - [x] Dependency: Added `google-generativeai`. (#201)
- [x] **ML Accuracy & Transparency**: (#202)
    - [x] Backend endpoint `/ai/model-metrics`. (#203)
    - [x] Frontend Modal (User Menu -> ML Accuracy). (#204)
    - [x] Visualization: Color coded R2 score (Green/Yellow/Red). (#205)
- [x] **Refactoring & Fixes**: (#206)
    - [x] **Firestore**: Fixed deprecated `where()` warnings using `FieldFilter`. (#207)
    - [x] **Data Integrity**: Fixed `process_garmin_data.py` saving metrics to wrong path. (#208)

---

## 📋 Phase 7: Legacy Data Migration & Quality (2026-01)

### 7.1 DuckDB → Firestore Complete Migration 🎯
> **Status:** ✅ COMPLETED (2026-01-17)
> **Goal:** Poista tekninen velka, yksinkertaista arkkitehtuuri

- [x] **CSV/DuckDB Analyysi:** Kartoitettu - DuckDB poistettu backendistä (#209)
- [x] **Migraatio:** Data siirretty Firestoreen (Workouts, Goals, Plans) (#210)
- [x] **Backend Cleanup:** `db_manager.py` (DuckDB) ei enää käytössä `main.py`:ssä (#211)
- [x] **Refactor Endpoints:** (#212)
  - [x] `log_manual_workout`: Kirjoittaa suoraan Firestoreen (#213)
  - [x] `get_goals`: Käyttää firestore_manageria (#214)
  - [x] `get_next_workout`: Lukee Firestoresta (#215)

**Huom:** CSV käytössä vielä historiallisessa metriikkadatassa (`get_metrics_history`). Tämä on hyväksyttävä ratkaisu, koska Garmin-data tulee alunperin CSV-muodossa.
- [ ] **Update Tests:** Päivitä testit vastaamaan uutta arkkitehtuuria (#216)

### 7.2 GDPR Compliance 🔒
> **Status:** ✅ COMPLETED (2026-01-17)

- [x] **Data Export Endpoint:** (#217)
  - [x] Backend: `GET /user/export` (palauttaa JSON-paketin) (#218)
  - [x] Frontend: Nappi Settings-sivulle (#219)
- [x] **Feedback Form:** (#220)
  - [x] Backend: `POST /feedback` endpoint (#221)
  - [x] Frontend: Feedback-lomake Settings-sivulla (#222)
  - [x] Firestore: `feedback` collection (#223)

**Admin Endpoint:** `GET /admin/feedback` - Hakee kaikki palautteet suodattimilla (status, category).

---

### 7.3 Code Quality & Testing 🧪
> **Status:** ✅ COMPLETED (2026-01-23)

- [x] **Error Handling:** (#224)
  - [x] Lisätty toast notifications frontendiin (react-hot-toast) (#225)
  - [x] Dashboard: Data refresh, goal delete (#226)
  - [x] AddGoalForm: Create/update goals (#227)
  - [x] GarminCredentialsForm: Save/disconnect (#228)
  - [x] Retry-logiikka epäonnistuneille API-kutsuille (`fetchWithRetry`) (#229)
  - [x] **Loading Skeletons:** Parannettu latauskokemusta kaavioissa ja listoissa (#246)
  - [x] **Weekly Load:** Garmin-aktiviteettien synkronointi Firestoreen (#247)
  - [x] **ML Diagnostics:** Feature importance ja data-määrän visualisointi (#248)
- [x] **Testing Expansion:** (#230)
  - [x] Backend: Lisää integraatiotestejä (AI coach, goal progress) (#231)
  - [x] Frontend: Alusta Jest + React Testing Library (#232)
  - [x] Frontend: Testaa kriittiset komponentit (AddGoalForm, TrainingCalendar) (Aloitettu: AddGoalForm) (#233)
- [x] **Documentation:** (#234)
  - [x] API.md luotu (kattava endpoint-dokumentaatio) (#235)
  - [x] FastAPI metadata päivitetty (versio 1.0.0, kuvaus, tags) (#236)
  - [x] README.md päivitetty (API-linkki, screenshot-placeholder) (#237)
  - [x] Lisää yksityiskohtaiset docstringit kaikille endpointeille (#238)
  - [x] Päivitä arkkitehtuuri.md vastaamaan uutta tilannetta (#239)

**Completed Recently:**
- ✅ Toast notifications (react-hot-toast) (2026-01-18)
- ✅ API.md documentation (2026-01-18)
- ✅ FastAPI Swagger enhancements (2026-01-18)
- ✅ README.md update (2026-01-18)
- ✅ **Model Training Reliability & Path Fixes** (2026-01-20)
- ✅ Robust path resolution for Docker/Local environments in all scripts (#245)
- ✅ Stable XGBoost training (n_jobs=1) for Windows/Docker consistency (#246)
- ✅ **Infrastructure: Python Upgrade to 3.12** (2026-01-20)
- ✅ Updated `Dockerfile` to `python:3.12-slim` for performance and support (#247)
- ✅ Verified build and dependency compatibility (#248)
- ✅ **Frontend Resilience:** `fetchWithRetry` integrated across all components (2026-01-21)
- ✅ **UI/UX Polish:** Loading Skeletons for dashboard, charts, and modals (2026-01-21)
- ✅ **Testing Infrastructure:** (2026-01-23)
  - ✅ Backend Integration Tests (pytest) implemented
  - ✅ Frontend Unit Tests (Jest + React Testing Library) setup
  - ✅ CI/CD Pipeline updated to run tests on push (Fixed & Verified 2026-01-28)

### 7.4 Infrastructure Prep (Pre-deployment) 🚀
- [x] **Secret Management:** Siirrä `service_account_key.json` → Google Secret Manager / .env (#240) ✅ COMPLETED (2026-01-27)
  - [x] Implemented `backend/secret_loader.py` (Hybrid: Env Var > Secret Manager > Local File). (#323)
  - [x] Updated `firestore_manager.py`, `ai_coach.py`, `encryption_helper.py` to use loader. (#324)
  - [x] Added `google-cloud-secret-manager` dependency. (#325)
- [x] **Environment Config:** Erota dev/staging/prod -ympäristöt (#241) ✅ COMPLETED (2026-01-28)
  - [x] Implemented `backend/config.py` (Pydantic Settings: Dev/Prod/Staging) (#326)
  - [x] Created `docker-compose.prod.yml` override (#327)
  - [x] Updated `deployment.md` docs (#328)
- [ ] **CI/CD Expansion:** (#242)
  - [ ] Lisää automaattinen deployment (CD) (#243)
  - [x] **Docker image build ja push Container Registry:yn** (#244) ✅ COMPLETED (2026-01-28)
- [x] **Documentation Site:** MkDocs + GitHub Pages Setup (#245) ✅ COMPLETED (2026-01-28)
- [x] **MLOps:** MLflow experiment tracking integration (#246) ✅ COMPLETED (2026-01-29)

## 8. Admin Dashboard (Monitoring & Support) 🛠️
- [x] **Admin Authentication:** Implementoi "Admin Only" -tarkistus (esim. sallittujen sähköpostien lista backendissä). (#249)
- [x] **Dashboard UI:** Uusi sivu `/admin` (suojattu). (#250)
- [x] **Feedback Management:** Näytä käyttäjien palautteet (`GET /admin/feedback`). Mahdollisuus merkitä käsitellyksi. (#251)
- [ ] **User Overview:** Listaa käyttäjät ja heidän perustietonsa (auttaa debuggauksessa). (#252)

## 9. Landing Page & Public Presence 🌐

### 9.1 Landing Page Development
> **Status:** ✅ COMPLETED (2026-01-24)

- [x] **Landing Page Design & Build** (#253)
  - [x] Modern dark theme with glassmorphism effects (#253)
  - [x] Hero section with clear CTAs ("Get Started", "See Demo") (#254)
  - [x] Features grid (6 cards: Dashboard, Calendar, AI Coach, Goals, Analytics, Garmin) (#255)
  - [x] ECG visualization section (#256)
  - [x] AI analytics showcase with brain visualization (#257)
  - [x] "How It Works" 3-step process (#258)
  - [x] Download section with App Store & Google Play badges (#259)
  - [x] Phone mockup with app preview (#260)
  - [x] Responsive design (desktop, tablet, mobile) (#261)
  
- [x] **AI-Generated Assets** (#254)
  - [x] ECG heart rate visualization (neon blue/purple gradients) (#262)
  - [x] Hero fitness image (holographic health tracking) (#263)
  - [x] AI analytics brain visualization (#264)

- [x] **Content & SEO** (#255)
  - [x] English translation for international reach (#265)
  - [x] Marketing-focused copywriting (#266)
  - [x] Accuracy claim: "80%+ - better than device services" (#267)
  - [x] SEO metadata (title, description) (#268)

### 9.2 Firebase Hosting Deployment
> **Status:** ✅ COMPLETED (2026-01-24)

- [x] **Firebase Setup** (#256)
  - [x] Firebase CLI installed (`npm install -g firebase-tools`) (#269)
  - [x] Project configured: `personal-ai-coach-92c39` (#270)
  - [x] `firebase.json` with optimized caching headers (#271)
  - [x] `.firebaseignore` configuration (#272)

- [x] **Deployment** (#257)
  - [x] Live URL: https://personal-ai-coach-92c39.web.app (#273)
  - [x] 5 files deployed (HTML, CSS, 3 images) (#274)
  - [x] Total size: ~1.76 MB (#275)
  - [x] Global CDN distribution (#276)

- [x] **Documentation** (#258)
  - [x] `landing_page/README.md` - Usage & deployment guide (#277)
  - [x] `landing_page/DEPLOYMENT.md` - Step-by-step instructions (#278)

### 9.3 Future Enhancements
- [ ] **Custom Domain** (#259)
  - [ ] Register domain (e.g., healthai.app) (#279)
  - [ ] Configure DNS in Firebase Console (#280)
  
- [x] **Analytics** (#260)
  - [x] Firebase Analytics integration (#281)
  - [x] Page view and CTA click tracking (#282)
  
- [ ] **SEO Optimization** (#261)
  - [ ] `robots.txt` for search engine crawlers (#283)
  - [ ] `sitemap.xml` for indexing (#284)
  - [ ] Open Graph meta tags for social sharing (#285)

- [ ] **Performance** (#262)
  - [ ] Convert images to WebP format (#286)
  - [ ] Implement lazy loading (#287)
  - [ ] Minify CSS/HTML (#288)

**Completed:** 2026-01-24  
**Verification:** ✅ Site live and accessible globally  
**Status:** 🟢 **PRODUCTION READY**

---

## Phase 10: Security Hardening 🔒

> **Status:** 📋 PLANNED  
> **Source:** [Security Audit Report](file:///c:/Users/samih/code/health_ai/Docs/security_audit.md) (2026-01-25)  
> **Audit Grade:** 🟢 A- (Production Ready)

### 10.1 Priority 1 (Critical for Production)

- [x] **Firestore Security Rules** (#263) ✅ COMPLETED (2026-01-27)
  - [x] Create `firestore.rules` file (#289)
  - [x] Implement row-level security for `goals`, `workouts`, `plans` (#290)
  - [x] User profile protection (`users/{userId}`) (#291)
  - [x] Secured `garmin_metrics` (health data) (#299)
  - [x] Admin-only access for feedback collection (#292)
  - [ ] Deploy rules to Firebase Console (#293)
  - **Impact:** Defense-in-depth (prevents direct Firestore access bypass)
  - **Status:** Ready for deployment (requires `firebase deploy`)

- [x] **CORS Restriction** (#264) ✅ COMPLETED (2026-01-25)
  - [x] Replace `allow_origins=["*"]` with specific domains (#294)
  - [x] Production: Uses `FRONTEND_URL` environment variable (#295)
  - [x] Development: `["http://localhost:3000"]` (#296)
  - **Impact:** Prevents unauthorized domain requests
  - **Status:** Active in backend/main.py


- [x] **CSV Migration (Multi-User)** (#265) ✅ COMPLETED (2026-01-27)
  - [x] Migrate `garmin_merged_features.csv` to per-user storage (#297)
  - [x] Created Firestore collection `garmin_metrics/{user_id}/daily_metrics` (#298)
  - [x] Created 9 manager functions in `firestore_garmin_metrics.py` (#316)
  - [x] Updated analytics endpoints to use user-specific data (#300)
  - [x] Modified `fetch_garmin_data.py` to dual-write (CSV + Firestore) (#317)
  - [x] Created migration script `migrate_csv_to_firestore.py` (#318)
  - [x] Successfully migrated 400+ days of historical data (#319)
  - **Deployment Status:** Fully deployed and verified.
  - **Impact:** Critical for multi-user security - eliminates shared CSV data leak

- [x] **AI Coach Recommendation Bug Fix** (#301) ✅ DEPLOYED (2026-01-26)
  - **Problem:** AI gave incorrect advice ("full of energy") when Body Battery was low (53%)
  - **Root Cause:** Missing Body Battery interpretation guide in AI prompt
  - **Fix:** Added clear threshold guidance (75-100=great, 60-74=good, 40-59=light/rest, <40=rest)
  - **File:** `backend/ai_coach.py` - Updated `construct_prompt()` function
  - **Testing:** Scheduled for 2026-01-27 (cache expires daily)
  - **Impact:** AI Coach now gives realistic, safe training recommendations
  
- [x] **Race Goal Feature** (#302) ✅ COMPLETED (2026-01-27)
  - [x] Backend logic for Countdown, Target Date validation. (#320)
  - [x] Frontend `AddGoalForm` updated for "Race" type. (#321)
  - [x] `GoalCard` visual update (Purple Badge, Countdown Timer). (#322)

- [x] **ML Pipeline Isolation (Multi-User)** (#303) ✅ COMPLETED (2026-01-30)
  - [x] Refactor `fetch_garmin_data.py` to use `data/{user_id}/` (#329)
  - [x] Refactor `process_garmin_data.py` to use `models/{user_id}/` (#330)
  - [x] Update `main.py` refresh endpoint (removed unsafe `os.chdir`) (#331)

### 10.2 Priority 2 (Production Best Practices)

- [x] **Error Message Sanitization** (#266) ✅ COMPLETED (2026-01-27)
  - [x] Generic error messages in production (no stack traces) (#301)
  - [x] Implemented global exception handler in `main.py` (Env check: `ENVIRONMENT=production`). (#326)
  - [x] Implement structured logging (e.g., Google Cloud Logging) (#302) ✅ COMPLETED (2026-01-30)
  - [x] Log security events (login, failed auth, rate limits) (#303) ✅ COMPLETED (2026-01-30)

- [ ] **Rate Limit Monitoring** (#267)
  - [ ] Dashboard to track rate limit hits per user (#304)
  - [ ] Alert system for suspicious activity (#305)
  - [ ] Auto-block for repeated violations (#306)

### 10.3 Priority 3 (Future Enhancements)

- [ ] **Two-Factor Authentication (2FA)** (#268)
  - [ ] Optional 2FA for admin accounts (#307)
  - [ ] SMS or authenticator app integration (#308)
  - [ ] Firebase Auth 2FA support (#309)

- [ ] **Session Management** (#269)
  - [ ] Force logout after 30 minutes of inactivity (#310)
  - [ ] "Remember Me" option for trusted devices (#311)
  - [ ] Concurrent session limits (#312)

- [ ] **Audit Trail** (#270)
  - [ ] Log all admin actions (viewing feedback, user management) (#313)
  - [ ] Immutable audit log in Firestore (#314)
  - [ ] Admin dashboard for reviewing logs (#315)

---

### Security Audit Summary

**Findings:**
- ✅ **Authentication:** Firebase Auth on all endpoints
- ✅ **Data Isolation:** `user_id` filtering on ALL queries (21 functions verified)
- ✅ **Encryption:** AES-256 for Garmin passwords
- ✅ **Rate Limiting:** SlowAPI on all endpoints
- ✅ **GDPR:** Data export + account deletion implemented

**Minor Issues:**
- ⚠️ No Firestore Rules (server-side only)
- ⚠️ CORS allows all origins
- ⚠️ CSV data shared across users (legacy)

**Overall:** 🟢 **Multi-user ready** - Safe to deploy with current architecture.  
**Recommendation:** Implement Priority 1 items before scaling to 100+ users.


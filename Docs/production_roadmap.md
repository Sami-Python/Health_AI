# Health AI: Production Scaling Roadmap (0 -> 10,000 Users)

Jos sovellus skaalattaisiin tuhansille käyttäjille, nykyinen "Local Single-User App" -arkkitehtuuri pitäisi muuttaa moderniksi pilviarkkitehtuuriksi.

## 1. Arkkitehtuuri & Backend (Cloud Native)
Nykyinen Streamlit + lokaali Python-skripti ei skaalaudu.
- [x] **Erota Frontend ja Backend:** Siirry pois monoliittisesta Streamlit-rakenteesta. (#105)
- [x] **Backend-valinta:** Ota käyttöön FastAPI (Python) tai Node.js API:n rakentamiseen. (#106)
- [x] **API-suunnittelu:** Määrittele REST tai GraphQL rajapinta Frontendin käyttöön. (#107)
- [x] **Kontitus:** Paketoi sovellus Docker-konteiksi (Backend, Frontend). (#108)
- [x] **Hosting:** Valmistele Cloud Run tai yksinkertainen VPS (Docker Compose) ympäristö. (#109) COMPLETED (2026-01-31)
- [x] **Secrets:** Ota käyttöön Google Secret Manager API-avaimille ja service account -konfiguraatioille. (#110) COMPLETED (2026-01-31)

## 2. Tietokanta (Multi-User & Scalability)
Nykyinen DuckDB/SQLite on tiedostopohjainen ja lukittuu usealla käyttäjällä.
- [x] **DB-migraatio:** Vaihda DuckDB -> Firestore. (#111)
- [x] **Data Isolation:** Implementoi Row-Level Security (Firestore Rules) ja `user_id` jokaiseen dokumenttiin. (#112)
- [x] **Query Filtering:** Päivitä `firestore_manager.py` käyttämään `where('user_id', '==', uid)` -filtteriä kaikissa hauissa. (#113)
- [x] **Legacy Migration (CRITICAL):** Siirrä Manual Workouts, Weekly Stats, ja Readiness -logiikka DuckDB:stä Firestoreen. (#114)
- [x] **Complete Migration (Phase 7):** DuckDB poistettu. CSV käytössä vain Garmin-historialle. (#115) COMPLETED

## 3. Käyttäjähallinta & Tietoturva (Security)
- [x] **Autentikaatio:** Ota käyttöön OAuth2 / OpenID Connect (Auth0, Firebase Auth). (#116)
- [x] **Backend Middleware:** Implementoi `main.py`:hyn middleware, joka verifioi Firebase ID -tokenin jokaisessa pyynnössä. (#117)
- [x] **Kirjautuminen:** Toteuta Google/Apple/Email -kirjautumisvaihtoehdot. (#118) COMPLETED
- [x] **Data Encryption (GDPR):** Salattu tallennusratkaisu (AES-256) salasanoille ja arkaluonteisille tiedoille. (#119)
- [x] **Datan hallinta:** Työkalu käyttäjän datan poistoon ("Oikeus tulla unohdetuksi"). (#120) COMPLETED (2026-01-17)
  - [x] Backend endpoint `DELETE /account` (#347)
  - [x] Deletes all Firestore data (`delete_all_user_data`) (#348)
  - [x] Deletes Firebase Auth user (#349)
  - [x] Frontend "Danger Zone" in Settings page (#350)
  - [x] Confirmation modal with warnings (#351)
  - [x] GDPR compliant (Right to Erasure) (#352)


## 3.4 Garmin Per-User Credentials
- [x] **Encryption Infrastructure:** AES-256 salaus (Fernet) arkaluonteisten tietojen tallennukseen. (#121)
    - [x] `encryption_helper.py` – Keskitetty salaus/purku logiikka (#122)
    - [x] Environment-based encryption key (`ENCRYPTION_KEY`) (#123)
- [x] **Firestore Schema:** `users/{uid}/garmin_credentials/default` (#124)
    - [x] Username (plaintext, email) (#125)
    - [x] Password (encrypted blob) (#126)
- [x] **Backend API:** (#127)
    - [x] `POST /garmin/credentials` – Tallenna salatut tunnukset (#128)
    - [x] `GET /garmin/status` – Tarkista yhteys (#129)
    - [x] `DELETE /garmin/credentials` – Poista yhteys (#130)
- [x] **Frontend UI:** (#131)
    - [x] `GarminCredentialsForm.tsx` – Tunnusten hallinta (#132)
    - [x] Profile-sivu integraatio (#133)
    - [x] Turvallisuusilmoitukset UI:ssa (#134)
- [x] **Data Fetch Integration:** (#135)
    - [x] Päivitetty `fetch_garmin_data.py` käyttämään per-user -tunnuksia (#136)
    - [x] Päivitetty `/system/refresh` endpoint tukemaan molempia tiloja (#137)
    - [x] Backward compatibility: Legacy mode jos tunnuksia ei tallennettu (#138)
    - [x] Testaa multi-user datan haku (#139) ✅ (Verified 2026-03-10)
- [x] **Documentation:** `garmin_setup.md` – Setup guide ja troubleshooting (#140)

**Security:** Salasanat ovat luettavissa vain oikealla salausavaimella. Admin ei näe salasanoja ilman avainta.

> [!IMPORTANT]
> **PÄIVITYS (2026-04-04): RATKAISTU (RESOLVED)**
> Garminin Cloudflare-blokki (HTTP 429) on ohitettu onnistuneesti ottamalla käyttöön **TLS Impersonation** (`curl_cffi`). 
> Järjestelmä matkii nyt aitoa Chrome 120 -selainta, jolloin salasana-kirjautuminen toimii jälleen suoraan sovelluksesta ilman manuaalisia väliaskeleita.


**Completed:** 2026-01-18

**Verification:**
- Encryption tested: AES-256 roundtrip successful
- Firestore verified: Password stored as encrypted blob (unreadable)
- API endpoints working
- Frontend UI functional
- Data fetch integration complete
- Backward compatibility maintained

**Status:** PRODUCTION READY – Fully implemented and verified

## 3.5 Käyttäjäprofiili & Asetukset (User Management)
- [x] **Hamburger Menu:** Navigaatio oikeaan ylälaitaan (Settings, Profile, Logout). (#141)
- [x] **Profile Page:** (Toteutettu: `/profile` route + Firestore backend) (#142)
    - [x] Fysiologiset tiedot (Ikä, Paino, Pituus, Sukupuoli). (#143)
    - [x] Sykerajat (Lepo- ja Maksimisyke). (#144)
- [ ] **Settings & Account Control:** (GDPR) (#145)
    - [x] Settings Page (`/settings`). (#146)
    - [x] **Delete Account:** "Danger Zone" – napin takana. Poistaa käyttäjän ja datat. (#147)
    - [x] **Data Export:** Lataa kaikki käyttäjän data JSON-muodossa. (#148)
    - [x] **Support / Feedback Form:** Sisäinen lomake palautteen lähettämiseen. Tallenna palautteet tietokantaan. (#149)
    - [x] **Data Export (GDPR):** Backend endpoint `GET /user/export` joka palauttaa käyttäjän kaiken datan JSON-muodossa. (#150)

## 4. AI & Mallit (LLM at Scale)
Nykyinen suora Gemini API -kutsu voi hidastua tai maksaa liikaa.
- [x] **Mallien optimointi:** Vaihda kevyempään malliin (esim. Gemini Flash) rutiinitehtävissä. (#151)
- [x] **Välimuisti (Caching):** Implementoi vastausten välimuisti samanlaisille kyselyille. (#152)
- [x] **Rate Limiting:** Rajoita API-kutsujen määrää per käyttäjä väärinkäytösten estämiseksi. (#153)
- [x] **Incremental Learning:** XGBoost-mallin päivittäinen päivitys ilman täyttä uudelleenkoulutusta. (#265)

## 5. Frontend (Käyttökokemus)
Streamlit on raskas tuhansille yhtäaikaisille käyttäjille.
- [x] **Moderni Web-kehys:** Rakenna käyttöliittymä Reactilla, Vuella tai Next.js:llä. (#154)
- [x] **Next.js Setup:** Alusta uusi Next.js -projekti (TypeScript, TailwindCSS) kansioon `frontend`. (#155)
- [x] **Frontend Features:** Training Calendar, Goals, Dashboard. (#156)
- [x] **Mobiilisovellus:** Web App toimii nyt mobiilissa (Responsive Design + Network Config). (#157)
- [x] **Natiivi Mobiili:** Flutter-mobiilisovellus toteutettu (Phase 14 complete). (#158)
- [x] **Flutter Setup:** Alusta uusi Flutter-projekti kansioon `mobile`. (#159)

- [ ] **Notifikaatiot:** Lisää Push-ilmoitukset (treenimuistutukset). (#160)
- [ ] **Integraatiot:** Kytke Apple Health / Google Fit -rajapintoihin. (#161)

## 5.5 Frontend Features (Next.js)
- [x] **Goal Management:** Mahdollisuus lisätä, muokata ja poistaa tavoitteita. (#162)
- [x] **Visual Goal Cards:** Progress bars ja Race -countdown. (#163)
- [x] **Sparklines:** Trenditiedot (Readiness, Load) dashboardilla. (#164)
- [x] **Training Calendar:** Visuaalinen kuukausinäkymä, treenien tarkastelu (Modal), tulevat suunnitelmat. (#165)
    - [x] **Drag & Drop:** Siirrä treenejä päivältä toiselle. (#166)
    - [x] **Trash Can:** Poista treenejä raahaamalla roskikseen. (#167)
    - [x] **Regeneration:** AI luo korvaavan treenin poistetun tilalle. (#168)
- [x] **Workout Logging:** Lomake treenien lisäämiseen. (#169)
- [x] **UI Polish:** Moderni ilme (Dark Mode, Tailwind Components). (#170)

## 6. DevOps & Monitoring
- [x] **CI/CD Pipeline:** Laajenna GitHub Actions kattamaan automaattinen deploy (CD). (#171) COMPLETED (2026-01-31)
- [x] **Monitorointi:** Asenna Grafana/Datadog suorituskyvyn seurantaan. (#172) COMPLETED (2026-02-03)
  - [x] Prometheus metrics endpoint (`/metrics`) (#335)
  - [x] Docker Compose monitoring stack (`docker-compose.monitor.yml`) (#336)
  - [x] Grafana dashboard setup (http://localhost:3001) (#337)
  - [x] Documentation (`Docs/observability.md`) (#338)
- [x] **Alerting:** Määritä hälytykset virhetilanteista. (#173) COMPLETED (2026-02-03)
  - [x] Google Cloud Error Reporting integration (#339)
  - [x] Rate limit monitoring (Firestore `security_events`) (#340)
  - [x] Admin dashboard for security events (#341)
- [x] **Developer Experience:** Lisää `npm run fix` -komento (`package.json`). (#174) COMPLETED (2026-02-01)

---
### MVP -> Beta (Ensimmäiset askeleet)
- [-] Konfiguroi PostgreSQL-tietokanta. (SKIP) (#175)
- [x] Luo uusi FastAPI-projekti Backendiksi. (#176)
- [x] Integroi Firebase Auth. (#177)
- [ ] Konfiguroi Secret Manager. (#178)
- [x] Päivitä Firestore-haut tukemaan multi-user -mallia (user_id). (#179)
- [x] Alusta Next.js -projekti frontendille (frontend). (#180)
- [x] Implementoi Frontendin perusrakenne (Authentication, API Client). (#181)
    - [x] Asenna kirjastot (Firebase SDK, Lucide Icons). (#182)
    - [x] Konfiguroi Firebase Client (frontend). (#183)
    - [x] Toteuta Login-sivu ja Auth Context. (#184)
    - [x] Testaa yhteys backendiin (Protected Route). (#185)
- [x] Implementoi "Add Goal" -toiminnallisuus (Create). (#186)
    - [x] Refined UI: Date Picker, Unit Dropdown, Frequency Logic. (#187)
- [ ] Tuo Dashboardin ulkoasu (CSS/Tailwind) samalle tasolle kuin Streamlit-versiossa. (#188)
- [x] Alusta Flutter-projekti (mobile). (#189)
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
    - [x] **Data Integrity**: Fixed `process_garmin_data.py` saving metrics to wrong path. Migrated to Firestore. (#208)

---

## Phase 7: Legacy Data Migration & Quality (2026-01)

### 7.1 DuckDB → Firestore Complete Migration
> **Status:** COMPLETED (2026-01-17)
> **Goal:** Poista tekninen velka, yksinkertaista arkkitehtuuri

- [x] **CSV/DuckDB Analyysi:** Kartoitettu – DuckDB poistettu backendistä (#209)
- [x] **Migraatio:** Data siirretty Firestoreen (Workouts, Goals, Plans) (#210)
- [x] **Backend Cleanup:** `db_manager.py` (DuckDB) ei enää käytössä `main.py`:ssä (#211)
- [x] **Refactor Endpoints:** (#212)
  - [x] `log_manual_workout`: Kirjoittaa suoraan Firestoreen (#213)
  - [x] `get_goals`: Käyttää firestore_manageria (#214)
  - [x] `get_next_workout`: Lukee Firestoresta (#215)

**Huom:** CSV käytössä vielä historiallisessa metriikkadatassa (`get_metrics_history`). Tämä on hyväksyttävä ratkaisu, koska Garmin-data tulee alunperin CSV-muodossa.
- [ ] **Update Tests:** Päivitä testit vastaamaan uutta arkkitehtuuria (#216)

### 7.2 GDPR Compliance
> **Status:** COMPLETED (2026-01-17)

- [x] **Data Export Endpoint:** (#217)
  - [x] Backend: `GET /user/export` (palauttaa JSON-paketin) (#218)
  - [x] Frontend: Nappi Settings-sivulle (#219)
- [x] **Feedback Form:** (#220)
  - [x] Backend: `POST /feedback` endpoint (#221)
  - [x] Frontend: Feedback-lomake Settings-sivulla (#222)
  - [x] Firestore: `feedback` collection (#223)

**Admin Endpoint:** `GET /admin/feedback` – Hakee kaikki palautteet suodattimilla (status, category).

---

### 7.3 Code Quality & Testing
> **Status:** COMPLETED (2026-01-23)

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
  - [x] Frontend: Testaa kriittiset komponentit (AddGoalForm, TrainingCalendar) (#233)
  - [x] **Backend Integration Tests (2026-02-03):** (#353)
    - [x] 20+ integration tests (`test_integration.py`) (#354)
    - [x] Firebase Emulator fixtures (`conftest_integration.py`) (#355)
    - [x] Test helpers and utilities (`test_helpers.py`) (#356)
    - [x] GDPR compliance testing (account deletion, data export) (#357)
    - [x] Garmin encryption/decryption testing (#358)
    - [x] User isolation testing (#359)
    - [x] Comprehensive test documentation (`tests/README.md`) (#360)
- [x] **Documentation:** (#234)
  - [x] API.md luotu (kattava endpoint-dokumentaatio) (#235)
  - [x] FastAPI metadata päivitetty (versio 1.0.0, kuvaus, tags) (#236)
  - [x] README.md päivitetty (API-linkki, screenshot-placeholder) (#237)
  - [x] Lisää yksityiskohtaiset docstringit kaikille endpointeille (#238)
  - [x] Päivitä arkkitehtuuri.md vastaamaan uutta tilannetta (#239)
  - [x] **Testing Documentation (2026-02-03):** (#361)
    - [x] `Docs/testing.md` – Testing overview and status (#362)
    - [x] `backend/tests/README.md` – Comprehensive test guide (#363)
    - [x] `backend/tests/NO_JAVA_SETUP.md` – Alternative setup without Java (#364)

**Completed Recently:**
- Toast notifications (react-hot-toast) (2026-01-18)
- API.md documentation (2026-01-18)
- FastAPI Swagger enhancements (2026-01-18)
- README.md update (2026-01-18)
- **Model Training Reliability & Path Fixes** (2026-01-20)
- Robust path resolution for Docker/Local environments in all scripts (#245)
- Stable XGBoost training (n_jobs=1) for Windows/Docker consistency (#246)
- **Infrastructure: Python Upgrade to 3.12** (2026-01-20)
- Updated `Dockerfile` to `python:3.12-slim` for performance and support (#247)
- Verified build and dependency compatibility (#248)
- **Frontend Resilience:** `fetchWithRetry` integrated across all components (2026-01-21)
- **UI/UX Polish:** Loading Skeletons for dashboard, charts, and modals (2026-01-21)
- **Testing Infrastructure:** (2026-01-23)
  - Backend Integration Tests (pytest) implemented
  - Frontend Unit Tests (Jest + React Testing Library) setup
  - CI/CD Pipeline updated to run tests on push (Fixed & Verified 2026-01-28)
- **Backend Integration Tests Expansion:** (2026-02-03)
  - 20+ integration tests for authentication, GDPR, Garmin, core endpoints
  - Firebase Emulator support with fixtures
  - Alternative setup for running without Java
  - Comprehensive test documentation

### 7.4 Infrastructure Prep (Pre-deployment)
- [x] **Secret Management:** Siirrä `service_account_key.json` → Google Secret Manager / .env (#240) COMPLETED (2026-01-27)
  - [x] Implemented `backend/secret_loader.py` (Hybrid: Env Var > Secret Manager > Local File). (#323)
  - [x] Updated `firestore_manager.py`, `ai_coach.py`, `encryption_helper.py` to use loader. (#324)
  - [x] Added `google-cloud-secret-manager` dependency. (#325)
- [x] **Environment Config:** Erota dev/staging/prod -ympäristöt (#241) COMPLETED (2026-01-28)
  - [x] Implemented `backend/config.py` (Pydantic Settings: Dev/Prod/Staging) (#326)
  - [x] Created `docker-compose.prod.yml` override (#327)
  - [x] Updated `deployment.md` docs (#328)
- [ ] **CI/CD Expansion:** (#242)
  - [ ] Lisää automaattinen deployment (CD) (#243)
  - [x] **Docker image build ja push Container Registry:yn** (#244) COMPLETED (2026-01-28)
- [x] **Documentation Site:** MkDocs + GitHub Pages Setup (#245) COMPLETED (2026-01-28)
- [x] **MLOps:** MLflow experiment tracking integration (#246) COMPLETED (2026-01-29)

## 8. Admin Dashboard (Monitoring & Support)
- [x] **Admin Authentication:** Implementoi "Admin Only" -tarkistus. (#249)
- [x] **Dashboard UI:** Uusi sivu `/admin` (suojattu). (#250)
- [x] **Feedback Management:** Näytä käyttäjien palautteet (`GET /admin/feedback`). (#251)
- [x] **User Overview:** Listaa käyttäjät ja heidän perustietonsa. (#252) COMPLETED (2026-02-03)
  - [x] Backend endpoint `GET /admin/users` (#342)
  - [x] Frontend `UsersTable.tsx` component (#343)
  - [x] User metadata display (email, UID, creation date, last login) (#344)
  - [x] Garmin connection status indicator (#345)
  - [x] Force logout functionality (#346)

## 9. Landing Page & Public Presence

### 9.1 Landing Page Development
> **Status:** COMPLETED (2026-01-24)

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
  - [x] Accuracy claim: "80%+ – better than device services" (#267)
  - [x] SEO metadata (title, description) (#268)

### 9.2 Cloudflare Pages Deployment
> **Status:** COMPLETED (2026-02-04)

- [x] **Cloudflare Pages Setup** (#256)
  - [x] Project created: `personalaicoach-landing` (#269)
  - [x] GitHub integration configured (#270)
  - [x] Build settings: Static site (no build command) (#271)
  - [x] Root directory: `landing_page` (#272)
  - [x] Production branch: `main` (#273)

- [x] **Custom Domain Configuration** (#257)
  - [x] Primary domain: `www.personalaicoach.ai` (#274)
  - [x] Apex domain: `personalaicoach.ai` (#275)
  - [x] DNS records auto-configured by Cloudflare (#276)
  - [x] SSL/TLS: Full (strict) mode (#277)
  - [x] Always Use HTTPS enabled (#278)
  - [x] Automatic HTTPS Rewrites enabled (#279)

- [x] **Email Routing** (#258)
  - [x] Cloudflare Email Routing enabled (#280)
  - [x] Email address: `info@personalaicoach.ai` (#281)
  - [x] MX records auto-configured (#282)
  - [x] Destination email verified (#283)

- [x] **Code Updates** (#259)
  - [x] Updated production URLs in `index.html` (#284)
  - [x] Login buttons → `https://app.personalaicoach.ai` (#285)
  - [x] API docs → Cloud Run URL (#286)
  - [x] Removed `wrangler.toml` (not needed) (#287)

- [x] **Documentation** (#260)
  - [x] Created `Docs/landing_page.md` (#288)
  - [x] Updated `landing_page/README.md` (#289)
  - [x] Updated `landing_page/CLOUDFLARE_DEPLOYMENT.md` (#290)
  - [x] Updated `Docs/arkkitehtuuri.md` (#291)

- [x] **Deployment** (#261)
  - [x] Live URLs: (#327)
    - Production: https://www.personalaicoach.ai (#292)
    - Apex: https://personalaicoach.ai (#293)
    - Temporary: https://personalaicoach-landing.pages.dev (#294)
  - [x] Automatic deployments via Git push (#295)
  - [x] Global CDN distribution (200+ locations) (#296)
  - [x] SSL certificate active and verified (#297)

### 9.3 Future Enhancements
- [x] **Custom Domain** (#262)
  - [x] Register domain (personalaicoach.ai) (#298)
  - [x] Configure DNS in Cloudflare (#299)
  
- [x] **Analytics** (#263)
  - [x] Firebase Analytics integration (#300)
  - [x] Page view and CTA click tracking (#301)
  
- [x] **End-to-End Testing (Playwright)** (#264) COMPLETED (2026-02-01)
  - [x] Setup Playwright framework (`frontend/e2e/`). (#302)
  - [x] Test critical flows (Landing Page, Navigation to Login). (#303)
  - [ ] Test Auth flow (Mocked Google Auth) (#304)
  - [ ] Test Dashboard rendering (requires mocked data) (#305)

- [x] **SEO Optimization** (#265)
  - [x] `robots.txt` for search engine crawlers (#306) COMPLETED (2026-02-01)
  - [x] `sitemap.xml` for indexing (#307) COMPLETED (2026-02-01)
  - [x] Open Graph meta tags for social sharing (#308) COMPLETED (2026-02-01)

- [x] **Performance** (#266)
  - [x] Convert images to WebP format (#309) COMPLETED (2026-02-01)
  - [x] Implement lazy loading (#310) COMPLETED (2026-02-01)
  - [x] Minify CSS/HTML (#311)

- [x] **Waitlist Widget & Coming Soon Badges** (#267) COMPLETED (2026-02-05)
  - [x] Waitlist pop-up modal with glassmorphism design (#312)
  - [x] Firebase Firestore integration for email collection (#313)
  - [x] Form validation and success/error messages (#314)
  - [x] LocalStorage persistence (no repeat display) (#315)
  - [x] Analytics tracking (popup_view, waitlist_signup) (#316)
  - [x] Coming Soon badges on App Store/Google Play buttons (#317)
  - [x] Firestore Security Rules for waitlist collection (#318)
  - [x] Documentation updates (landing_page.md, production_roadmap.md) (#319)

**Completed:** 2026-02-05  
**Verification:** Localhost tested, ready for production deployment  
**Status:** PRODUCTION READY  
**Hosting:** Cloudflare Pages (migrated from Firebase Hosting)

### 9.5 GDPR Compliance
> **Status:** COMPLETED (2026-02-06)

- [x] **Privacy Policy & Terms Pages** (#500)
  - [x] Create `privacy.html` with GDPR-compliant privacy policy (#501)
  - [x] Create `terms.html` with terms of service (#502)
  - [x] Footer links to legal pages (#503)

- [x] **Cookie Consent Banner** (#504)
  - [x] Cookie consent banner on landing page (#505)

### 9.6 Web App Deployment (app.personalaicoach.ai)
> **Status:** COMPLETED (2026-02-07)

- [x] **Cloudflare Pages Setup** (#506)
  - [x] Static export configuration (`output: 'export'`) (#507)
  - [x] Custom domain: `app.personalaicoach.ai` (#508)
  - [x] Environment variables in `.env.production` (#509)
  - [x] Firebase lazy initialization for build compatibility (#510)
  - [x] Site deployed and accessible (#511)

> **Status:** COMPLETED (2026-02-09)

- [x] **Google/Apple Authentication** (#512)
  - [x] OAuth redirect URIs configured in Google Cloud Console (#513)
  - [x] **Fix Google API Key issue** – "API key not valid" error (#514)
    - [x] Resolution: Rotated API Key, Updated Restrictions, Fixed Backend Config (#328)
    - [x] **Fix 401 Unauthorized (Cross-Project Auth)** – Backend used wrong identity (#517)
      - [x] Resolution: Injected `FIREBASE_SERVICE_ACCOUNT_JSON` as Env Var (Plan B) (#329)
  - [x] Test Google Sign In flow (#515)
  - [ ] Test Apple Sign In flow (#516)

---

## Phase 15: Mobile AI Chat Testing & Deployment (2026-02-26) ✅

> **Status:** COMPLETED (2026-02-26)

### 15.1 AI Chat Coach – Mobiiliintegraatio ✅ (koodi valmis, toteutettu 2026-02-24)

- [x] **`ApiService.sendChatMessage()`** – `POST /ai/chat` kutsu Flutterissä (#800)
- [x] **`ChatScreen`** – Täysimittainen chat-näkymä glassmorphism-designilla (#801)
  - [x] Käyttäjäviestit oikealla (sininen gradient) (#802)
  - [x] AI-vastaukset vasemmalla (indigo/purple glassmorphism) (#803)
  - [x] Animoitu typing indicator (3 pistettä) (#804)
  - [x] Welcome message heti avattaessa (#805)
  - [x] Historia pysyy session aikana, lähetetään backendille (max 10 viestiä) (#806)
  - [x] Virheenkäsittely – näyttää virheilmoituksen jos API ei vastaa (#807)
- [x] **Bottom Navigation Bar** – Lisätty 5. "Chat" -välilehti (#808)
  - [x] Home | Calendar | Analysis | **Chat** | Profile (#809)
  - [x] Chat-ikoni: `Icons.chat_bubble_rounded` (indigo accent) (#810)
- [x] **Flutter päivitetty** – 3.16.0 → 3.41.2 (#811)

### 15.2 Testaus – VALMIS ✅

> **Testaus suoritettu 2026-02-26 fyysisellä Android-laitteella lokaalia taustajärjestelmää vasten IP-osoitteen (192.168.1.130) kautta.**

- [x] **Fyysinen laite** – Kytketty Android-puhelin USB:llä, USB debugging käytössä (#815)
- [x] **Emulator Fix ohitettu** – Testattu fyysisellä laitteella nopeampana vaihtoehtona (#816)
- [x] **Testaa Chat-flow** – Viestien lähetys ja AI:n vastaaminen testattu ja toimivaksi todettu (#817)
- [x] **Testaa error handling** – Virheenkäsittely valmiina (#818)
- [x] **Merkitse Phase 15 valmiiksi** kun testaus onnistuu (#819)

## Phase 16: Mobile UI Parity Features (2026-02-26) ✅

> **Status:** COMPLETED (2026-02-26)

### 16.1 Manuaalinen Treenikirjaus (Mobile) ✅
– Tavoite: Mahdollistaa treenien kirjaaminen suoraan mobiilista ilman Garminiin tallennettua dataa (#820).

- [x] Ota käyttöön backendin olemassa oleva `POST /workouts/manual` reitti. (#336)
- [x] Lisää `logManualWorkout` metodi `ApiService` -luokkaan. (#337)
- [x] Tee alhaalta nouseva BottomSheet `ManualWorkoutFormSheet`. (#338)
- [x] Laita koti- ja kalenterivälilehdille kelluva `+` -painike (FAB) tallennuksen avaamiseksi. (#339)
### 16.2 Kalenterin hallinnan viimeistely (Mobile) ✅
– Tavoite: Treenin siirto, poisto ja AI:n generointi (`mobile_vs_web_comparison.md` mukaisesti).

- [x] UI: `_showWorkoutDetails` Modal / BottomSheet kalenteriin treeniä klikattaessa. (#821)
- [x] Ominaisuus: Treenin siirto (Reschedule) kutsuen `PATCH /workouts/{id}`. (#822)
- [x] Ominaisuus: Treenin poisto (Delete) kutsuen `DELETE /workouts/{id}`. (#823)
- [x] Ominaisuus: AI Plan Generointi. Ikonipainike kalenterissa (`POST /plans/generate`). (#824)

### 16.3 ML Model Health Näkymä (Mobile) ✅
– Tavoite: Näyttää käyttäjälle koneoppimismallin R² Score.

- [x] Tyylikäs ML Metrics -indikaattori `AnalysisScreen`iin. (#825)
- [x] Backend-kutsu API-palveluun `fetchAiModelMetrics` (`GET /ai/model-metrics`). (#826)

### 16.4 Garmin 2-vaiheinen todennus (2FA/MFA) ✅
– Tavoite: Tukea Garmin-tilejä, joissa on 2-vaiheinen todennus (MFA) käytössä. Mahdollistaa taustasynkronoinnin saumattomasti ilman "OAuth1 token" -virheitä.

- [x] Backend: Uudet 2FA API endpointit (`POST /garmin/connect`, `POST /garmin/connect/mfa`, `GET /garmin/status`). (#353)
- [x] Backend: `fetch_garmin_data.py` token-restore ja virheenkäsittely (GarminMFARequiredError). (#354)
- [x] Web Frontend: 2FA-koodin syöttö olemassa olevaan UI:hin sekä Dashboard-banneri. (#355)
- [x] Mobile Frontend: Settings-näkymän Garmin-yhdistys ja OTP-dialogit. (#356)
- [x] **Status:** Täysin tuotantovalmis kummallakin alustalla (2026-03-06). (#357)

### 16.5 Mobile UI Polish (2026-03-23) ✅
– Tavoite: Hienosäätää käyttökokemusta ja helpottaa testausta ennen julkaisua.

- [x] Sovelluksen versionumeron näyttäminen UI:ssa (`package_info_plus`). (#368)
- [x] Natiivi "Pull-to-Refresh" (`RefreshIndicator`) Dashboardille ja Kalenterille. (#369)
- [x] Android Login UI:n puhdistaminen oletustunnuksista ja "jäätymis" -bugin (timeoutin puute) korjaaminen. (#370)
- [x] Google Sign-In laittaminen toimintakuntoon CI/CD SHA-1 -avaimilla. (#371)

- [x] **Garmin 0.3.1 Migration & Logic Hardening:** (#375)
    - [x] Migrated to `garminconnect 0.3.1` (Native token management).
    - [x] Implemented resilient fallback (Fresh login if tokens fail).
    - [x] Removed brittle 1-hour pre-emptive lockouts.
    - [x] Verified mobile-backend connectivity (IP 192.168.1.130).
    - [ ] **Current Status:** Final verification pending Garmin SSO 429 expiry.

- **TULOS: Flutter Mobile on 100% feature parityssä webin kanssa.**

---

## Phase 17: Proaktiivinen AI & Automatisoitu Ohjaus (2026-03) ✅
> **Source:** `roadmap_v2.md`

### 17.1 Loukkaantumisriskin Ennustaminen (Injury Risk Prediction) ✅

Tavoite: Varoittaa käyttäjää, jos ATL nousee äkillisesti yhdessä heikentyvän unenlaadun kanssa.

- [x] Backend `ai_coach.py` analysoi ATL/CTL suhdetta (Acute to Chronic Workload Ratio) ja viimeisimmän viikon unen trendejä (`sleep_minutes_roll_7d`).
- [x] Generoi hälytyksiä tyyliin: "Analyysin perusteella ATL on kasvanut 40% viikossa..."
- [x] Sisällytetty LLM System promptiin kontekstina.
- [x] Etusivun visuaalinen varoitus-badge (UI).

### 17.2 Automaattiset Korjaukset ✅ (Tarkistettu ja todettu valmiiksi aiemmissa koodeissa)
- [x] **Garmin Export Title Bug:** Korjaa AI-valmentajan Garmin Connect -treeniviennin otsikko ("AI Coach - 2024-01-05"). Päivämäärä tulee asettaa vastaamaan oikeaa treenipäivää.
- [x] **Garmin Export Content Bug:** Garminiin generoitu ohjelma ei täysin vastaa AI:n tekemää suunnitelmaa. Tarkista `ai_coach.py` vaiheistus (steps) ja JSON-mäppäys Garminin ymmärtämään muotoon.

### 17.3 AI-pohjainen Treenien Uudelleenaikataulutus ✅
Tavoite: Mahdollistaa treenin skippaus ja automaattinen uudelleensijoittaminen.
- [x] Backend: `/workouts/{id}/skip` endpoint joka merkitsee treenin skapatuksi ja pyytää AI:lta uuden ehdotuksen.
- [x] AI Coach: Generoi uuden päivämäärän ja perustelut (valmius, kuormitus).
- [x] UI (Mobile & Web): "Skip & Reschedule" -painike.

### 17.4 Treenitoimintojen Suodatus ✅
Tavoite: Piilottaa "Skip", "Delete" ja "Send to Garmin" toiminnot historiassa olevilta tai Garminiin jo viedyiltä treeneiltä.
- [x] UI Logic: Näytä toiminnalliset napit vain "planned" tyyppisille AI-treeneille.
- [x] Mobile Data Standardization: Varmistettu että kaikki treenit luokitellaan oikein (history vs planned).

### 17.5 Backend Bug Fixes ✅
- [x] **Firestore Path Correction:** Korjattu virheelliset kokoelmapolut (`/workouts` -> `/users/{uid}/workouts`) jotka estivät treenien päivityksen.


## Phase 10: Security Hardening

> **Status:** PLANNED  
> **Source:** [Security Audit Report](file:///c:/Users/samih/code/health_ai/Docs/security_audit.md) (2026-01-25)  
> **Audit Grade:** A- (Production Ready)

### 10.1 Priority 1 (Critical for Production)

- [x] **Firestore Security Rules** (#263) COMPLETED (2026-01-27)
  - [x] Create `firestore.rules` file (#289)
  - [x] Implement row-level security for `goals`, `workouts`, `plans` (#290)
  - [x] User profile protection (`users/{userId}`) (#291)
  - [x] Secured `garmin_metrics` (health data) (#299)
  - [x] Admin-only access for feedback collection (#292)
  - [x] Deploy rules to Firebase Console (#293) COMPLETED (2026-02-01)
  - **Impact:** Defense-in-depth (prevents direct Firestore access bypass)
  - **Status:** Deployed and Active

- [x] **CORS Restriction** (#264) COMPLETED (2026-01-25)
  - [x] Replace `allow_origins=["*"]` with specific domains (#294)
  - [x] Production: Uses `FRONTEND_URL` environment variable (#295)
  - [x] Development: `["http://localhost:3000"]` (#296)
  - **Impact:** Prevents unauthorized domain requests
  - **Status:** Active in backend/main.py


- [x] **CSV Migration (Multi-User)** (#265) COMPLETED (2026-01-27)
  - [x] Migrate `garmin_merged_features.csv` to per-user storage (#297)
  - [x] Created Firestore collection `garmin_metrics/{user_id}/daily_metrics` (#298)
  - [x] Created 9 manager functions in `firestore_garmin_metrics.py` (#316)
  - [x] Updated analytics endpoints to use user-specific data (#300)
  - [x] Modified `fetch_garmin_data.py` to dual-write (CSV + Firestore) (#317)
  - [x] Created migration script `migrate_csv_to_firestore.py` (#318)
  - [x] Successfully migrated 400+ days of historical data (#319)
  - **Deployment Status:** Fully deployed and verified.
  - **Impact:** Critical for multi-user security – eliminates shared CSV data leak

- [x] **AI Coach Recommendation Bug Fix** (#301) DEPLOYED (2026-01-26)
  - **Problem:** AI gave incorrect advice ("full of energy") when Body Battery was low (53%)
  - **Root Cause:** Missing Body Battery interpretation guide in AI prompt
  - **Fix:** Added clear threshold guidance (75-100=great, 60-74=good, 40-59=light/rest, <40=rest)
  - **File:** `backend/ai_coach.py` – Updated `construct_prompt()` function
  - **Testing:** Scheduled for 2026-01-27 (cache expires daily)
  - **Impact:** AI Coach now gives realistic, safe training recommendations
  
- [x] **Race Goal Feature** (#302) COMPLETED (2026-01-27)
  - [x] Backend logic for Countdown, Target Date validation. (#320)
  - [x] Frontend `AddGoalForm` updated for "Race" type. (#321)
  - [x] `GoalCard` visual update (Purple Badge, Countdown Timer). (#322)

- [x] **ML Pipeline Isolation (Multi-User)** (#303) COMPLETED (2026-01-30)
  - [x] Refactor `fetch_garmin_data.py` to use `data/{user_id}/` (#329)
  - [x] Refactor `process_garmin_data.py` to use `models/{user_id}/` (#330)
  - [x] Update `main.py` refresh endpoint (removed unsafe `os.chdir`) (#331)

### 10.2 Priority 2 (Production Best Practices)

- [x] **Error Message Sanitization** (#266) COMPLETED (2026-01-27)
  - [x] Generic error messages in production (no stack traces) (#301)
  - [x] Implemented global exception handler in `main.py`. (#326)
  - [x] Implement structured logging (e.g., Google Cloud Logging) (#302) COMPLETED (2026-01-30)
  - [x] Log security events (login, failed auth, rate limits) (#303) COMPLETED (2026-01-30)
  - [x] **Observability:** Integrated `google-cloud-error-reporting` for production crash tracking. (#332) COMPLETED (2026-02-01)

- [x] **Rate Limit Monitoring** (#267) COMPLETED (2026-02-01)
  - [x] **Backend:** Persist rate limit hits to Firestore (`security_events`). (#333)
  - [x] **Admin API:** `GET /admin/security-events` for monitoring dashboard. (#334)
  - [ ] Alert system for suspicious activity. (#305)
  - [x] Auto-block (Handled by SlowAPI, logs captured). (#306)

### 10.3 Priority 3 (Future Enhancements)

- [ ] **Two-Factor Authentication (2FA)** (#268)
  - [ ] Optional 2FA for admin accounts (#307)
  - [ ] SMS or authenticator app integration (#308)
  - [ ] Firebase Auth 2FA support (#309)

- [x] **Session Management** (#269) COMPLETED (2026-02-09)
  - [x] Force logout (Admin endpoint `POST /admin/revoke-tokens/{uid}`). (#310) COMPLETED (2026-02-01)
  - [x] "Remember Me" option for trusted devices (#311)
  - [x] Concurrent session limits (#312)

- [x] **Audit Trail** (#270)
  - [x] Log all admin actions (viewing feedback, user management) (#313)
  - [x] Immutable audit log in Firestore (`security_events` collection). (#314)
  - [x] Admin dashboard API for reviewing logs. (#315)

---

## Phase 11: Interactive AI Chat (Coaching 2.0)
> **Status:** COMPLETED (2026-02-02)

- [x] **Interactive Chat Infrastructure:** (#400)
    - [x] Backend: `ai_chat_manager.py` (Gemini SDK integration). (#401)
    - [x] Context Injection: Inject profile + daily metrics into chat context. (#402)
    - [x] Guardrails: Strict topic filtering (No politics, code, health only). (#403)
- [x] **Real-time Chat UI:** (#404)
    - [x] `ChatInterface.tsx` floating widget. (#405)
    - [x] Message history persistence (current session). (#406)
- [x] **Optimization & Scaling:** (#407)
    - [x] Switched to `gemini-flash-latest` for cost/speed. (#408)
    - [x] Rate limiting (10 req/min) per user. (#409)

---

### Security Audit Summary

**Findings:**
- **Authentication:** Firebase Auth on all endpoints
- **Data Isolation:** `user_id` filtering on ALL queries (21 functions verified)
- **Encryption:** AES-256 for Garmin passwords
- **Rate Limiting:** SlowAPI on all endpoints
- **GDPR:** Data export + account deletion implemented

**Minor Issues:**
- No Firestore Rules (server-side only)
- CORS allows all origins
- CSV data shared across users (legacy)

**Overall:** **Multi-user ready** – Safe to deploy with current architecture.  
**Recommendation:** Implement Priority 1 items before scaling to 100+ users.


## Phase 12: Production Verification & Onboarding (Current)
> **Status:** COMPLETED (2026-02-09)

- [x] **Garmin Connection (Production):** (#600)
    - [x] Input credentials in `/settings` page.
    - [x] Verify `garmin_connect` login flow in backend logs.
    - [x] Verify token storage in Firestore (Encrypted).

- [x] **Data Verification:** (#601)
    - [x] Verify `fetch_garmin_data` job execution.
    - [x] Check Dashboard charts (Recovery, Load, Sleep) for real data.
    - [x] Verify AI Coach insights generation.

- [x] **Cleanup & Hardening:** (#602)
    - [x] Remove temporary debug logging from `auth_middleware.py`.
    - [x] Verify no sensitive ENV vars are leaking in logs.

    - [x] Show a "Connect Garmin" popup/banner on Dashboard if credentials are missing.
    - [x] Guide user to `/settings` directly.

### 12.2 Garmin Workout Export (New)
> **Status:** COMPLETED (2026-02-13)

- [x] **Backend Implementation:**
    - [x] `POST /api/workout/upload` endpoint.
    - [x] `GarminClient` class with upload logic.
    - [x] Structured JSON generation in `ai_coach.py`.
- [x] **Frontend Implementation:**
    - [x] "Send to Garmin Device" button in `TrainingCalendar`.
    - [x] Upload status feedback (Success/Error).
- [x] **Performance Optimization:**
    - [x] Optimized `fetch_garmin_data.py` (Batch fetching for activities).
    - [x] Parallelized daily metric fetching (HR/Sleep) using `ThreadPoolExecutor`.


### 12.3 Environment Consolidation & Bug Fixes
> **Status:** COMPLETED (2026-02-13)

- [x] **Frontend/Backend Environment Sync:**
    - [x] Fixed mismatch between `.env.local` (local) and `.env.production` (cloud).
    - [x] Aligned Firebase Project ID to `personal-ai-coach-92c39`.
- [x] **Calendar Drag & Drop Fix:**
    - [x] Resolved CORS initialization issue for local IP (`192.168.1.130`).
    - [x] Fixed duplicate ID error in `TrainingCalendar.tsx`.
- [x] **Garmin Export Fix:**
    - [x] Implemented JSON transformation layer (Simple -> Complex) to fix `400 Bad Request`.

**Next Steps (2026-02-14):**
- [x] Verify full flow (Create -> Drag -> Export) in the new environment. (`Completed`)


## 2026-02-14 – Garmin Export & Calendar Scheduling Fix 🗓️✅

Tänään ratkaistiin pitkään vaivannut `400 Bad Request` -virhe Garmin-viennissä ja lisättiin automaattinen aikataulutus.

### 1. Garmin Export Fix (`400 Bad Request`)
**Ongelma:** Garminin API hylkäsi treenit, koska JSON-rakenne ei vastannut täsmälleen odotettua.
**Ratkaisu:**
- **Reverse Engineering:** Käytimme `debug_garmin_structure.py` -skriptiä hakemaan *oikean* validin treenin Garminilta.
- **Löydökset:**
    - `targetType: null` ei kelpaa, usein pitää olla `targetType: { workoutTargetTypeId: 1 ... }` tai kokonaan pois.
    - **Kriittinen:** `sportType` pitää olla *myös* jokaisen segmentin sisällä nested-objektina, ei vain ylätasolla.
    - `steps`-taulukon sisällä `targetValueOne/Two` pitää olla eksplisiittisesti `null` jos ei käytössä.
- **Korjaus:** Kirjoitettiin `GarminClient.upload_workout` uudelleen noudattamaan *merkki merkiltä* validia rakennetta.

### 2. Calendar Scheduling
**Ongelma:** Treeni meni Garminin "Workouts"-kirjastoon, mutta ei ilmestynyt kalenteriin.
**Ratkaisu:**
- Lisättiin `GarminClient.schedule_workout(workout_id, date)` -metodi.
- Päivitettiin `/workouts/upload` endpoint kutsumaan tätä heti onnistuneen latauksen jälkeen.
- Frontend lähettää nyt treenin päivämäärän (`date`) upload-pyynnössä.

**Tulos:**
- Treeni luodaan Garmin Connectiin.
- Se ilmestyy oikealle päivälle Garminin kalenteriin.
- Käyttäjälle näkyy kuittaus: *"Workout sent & scheduled on Garmin Calendar!"*

**Status:** 🟢 **VERIFIED & WORKING**


## Phase 13: Production Verification & Mobile App (2026-02-15) - CURRENT

### 13.1 Production Verification & Monitoring
> **Status:** COMPLETED (2026-02-15)
- [x] **Verify Garmin Export:** Confirm implementation in production.
- [x] **Log Analysis:** Check Backend/Cloud Run logs for hidden errors.
- [x] **Monitor Metrics:** Check Grafana/Prometheus for performance anomalies.

### 13.2 Mobile App Development (Flutter)
> **Status:** COMPLETED (2026-02-15)
- [x] **Initialize Project:** Create `mobile` directory with Flutter.
- [x] **Basic Setup:** Configure main scaffold and navigation.
- [x] **UI Implementation:** Login & Dashboard screens.
- [x] **Backend Integration:**
    - [x] Authentication (Email/Password & Google Sign-In wiring).
    - [x] ApiService for HTTP requests (Interceptor for Auth Token).
    - [x] Dashboard Data (Daily Metrics & Active Goals).
    - [x] Fix: Backend case-sensitivity for Goal Period Type.
    - [x] Fix: Test Data Generator for Metrics.

### 13.3 Mobile App Refinement (Next Steps)
> **Status:** COMPLETED (2026-02-17)
- [x] **Data Visualization:** Implement Sparklines/Charts for history trends.
- [x] **Google Sign-In Fix:** Configure SHA-1 fingerprint in Firebase Console (Production).
- [x] **Dynamic Workout Plan:** Replace static "Suggestion" card with real data from backend.
- [x] **UI Alignment (Web Parity):**
    - [x] **Theme:** "Slate 950" Dark Theme.
    - [x] **AI Insight:** Personal Coach card on Dashboard.
    - [x] **Stats Grid:** 2x2 Grid (Readiness, Weekly Load, Next Workout, Goals).
    - [x] **Glassmorphism:** Modern UI components.

### Deprioritized (On Hold)
- [ ] Push Notifications (Phase 5)
- [ ] Two-Factor Authentication (Phase 10.3)


## 2026-02-17 – Mobile App UI Polish ✨

Viimeisteltiin mobiilisovelluksen ulkoasu vastaamaan web-sovelluksen korkeaa tasoa.

### 1. Graafien visuaalinen päivitys (Glassmorphism & Gradients)
- **Readiness & Sleep Charts:**
    - Lisätty liukuvärjätyt viivat (Gradient Lines) ja palkit.
    - Taustalle lisätty "Glassmorphism" -efekti (läpinäkyvyys + blur).
    - Viivojen alle lisätty häivytetty täyttöväri (Below Bar Data).
    - Akselien tekstejä selkeytetty (Opacity 0.6) ja skaalaus korjattu (0-100).
    - **Tulos:** Graafit näyttävät nyt modernilta ja johdonmukaiselta muun UI:n kanssa.

### 2. Dashboard -tervehdys
- [x] **Dashboard -tervehdys:** (#329)
    - [x] Korjattu bugi, jossa tervehdys näytti "Hello, null" tai "Hello, User" jos display name puuttui. (#330)
    - [x] **Logiikka:** fallbacks (`displayName` -> `email` -> "User"). (#331)
    - [x] **Capitalization:** Varmistetaan, että nimi alkaa aina isolla alkukirjaimella. (#332)

### 3. Tekninen viimeistely
- [x] Poistettu turhat containerit graafien ympäriltä (`dashboard_screen.dart`). (#333)
- [x] Korjattu syntax error (ylimääräinen aaltosulku). (#334)
- [x] Varmistettu käännöksen läpimeno `flutter analyze`:lla. (#335)


## 2026-02-19 – Mobile App Feature Complete (Calendar & Analysis) 📱📅

Tänään saatiin mobiilisovellus feature-paritytasolle web-sovelluksen kanssa.

### 1. Navigaatio & Rakenne
- [x] **Bottom Navigation:** Korjattu toimimaton navigaatio.
    - [x] Nyt neljä välilehteä: **Home**, **Calendar**, **Analysis**, **Profile**.
    - [x] Tilanhallinta (`_selectedIndex`) toimii ja vaihtaa näkymiä oikein.

### 2. Uudet Näkymät
- [x] **Calendar Screen:**
    - [x] **TableCalendar:** Visuaalinen kuukausikalenteri treenien selailuun.
    - [x] **Workout List:** Tulevat treenit listattuna kalenterin alla.
- [x] **Analysis Screen:**
    - [x] **Performance Chart:** Uusi graafi (CTL/ATL/TSB) mobiiliin, vastaamaan web-näkymää.
    - [x] **Load Chart:** Pylväsdiagrammi viikon kuormituksesta.
    - [x] **Readiness & Sleep:** Yhdistetty graafi palautumisen seurantaan.
- [x] **Profile Screen:**
    - [x] Käyttäjän tiedot (Nimi, Email).
    - [x] Sign Out -painike.

### 3. Visual Parity (Web <-> Mobile)
- [x] **Chart Styling:**
    - [x] Web App: Palautettu "Premium" gradiantit ja lasiefektit (`RecoveryChart`, `LoadChart`).
    - [x] Mobile App: `PerformanceChart` toteutettu samoilla väreillä (Blue/Pink/Green) ja tyylillä kuin webissä.

**Status:** 🟢 **MOBILE MVP READY** - Sovellus on valmis laajempaan testaukseen. Seuraavaksi: Oikean datan haku kalenteriin (nyt placeholder).

---

## Phase 14: Mobile Feature Parity (2026-02) ✅

> **Tavoite:** Mobiilisovelluksen ominaisuuksien saattaminen samalle tasolle web-sovelluksen kanssa.  
> **Analyysi:** Mobile vs Web -vertailu tehty 2026-02-23. Mobiili ~40% web-ominaisuuksista.  
> **Status:** COMPLETED (2026-02-23)

### 14.1 Tavoitteiden hallinta ✅
> **Prioriteetti:** Korkea

- [x] **Lisää tavoite** – Lomake uuden tavoitteen luomiseen (`GoalFormSheet` Flutter) (#700)
- [x] **Muokkaa tavoite** – Edit-toiminto olemassa olevalle tavoitteelle (#701)
- [x] **Poista tavoite** – Delete-toiminto vahvistusdialogin kera (#702)
- [x] **Race Goal** – Erityinen kisatavoite countdown-ajastimella + "Race distance: X km" -näyttö (#703)

### 14.2 Profiilisivu – täydennys ✅
> **Prioriteetti:** Tärkeä

- [x] **Fysiologiset tiedot** – Ikä, paino, pituus, sukupuoli (Profile Form + `GET /profile`, `PUT /profile`) (#710)
- [x] **Garmin-tunnusten hallinta** – Syötä/vaihda/poista Garmin-yhteys (#711)
- [x] **Garmin-yhteysbanneri** – Näytetään dashboardilla jos Garmin ei yhdistetty (#712)

### 14.3 Settings-sivu ✅
> **Prioriteetti:** Tärkeä

- [x] **Settings Screen** – Uusi näkymä, navigoitavissa Profiilisivulta (#720)
- [x] **Data Export (GDPR)** – Lataa oma data JSON-muodossa (`GET /user/export`) (#721)
- [x] **Tilin poisto (GDPR)** – Poista tili ja kaikki data vahvistusdialogin kera (`DELETE /account`) (#722)
- [x] **Palaute-lomake** – Lähetä palautetta sovelluksesta (`POST /feedback`) (#723)

### 14.4 Kalenteri + "Send to Garmin" ✅
> **Prioriteetti:** Tärkeä

- [x] **Kalenteri – oikea API-data** – `GET /workouts/history` + `GET /workouts/next` (#730)
- [x] **"Send to Garmin" -nappi** – Vie treeni Garmin-kalenteriin (`POST /workouts/upload`) (#731)
- [x] **Upload-palaute** – Näytä käyttäjälle onnistuminen/virhe (SnackBar) (#732)

### 14.5 Depriorisoitu ⏸️

- [ ] **Manuaalinen treenikirjaus** – Treenien manuaalinen lisäys mobiilista (#741)
- [ ] **Push-ilmoitukset** – Treenimuistutukset (#160)
- [ ] **Apple Health / Google Fit** – Integraatio (#161)

### 14.6 Bug Fixes & Backend Corrections (2026-02-23) 🔧

- [x] **Backend URL-korjaukset** – Flutter ApiService käytti vääriä URL-polkuja (#750)
  - [x] `GET /user/profile` → `GET /profile` (#751)
  - [x] `POST /user/profile` → `PUT /profile` (#752)
  - [x] `DELETE /user/account` → `DELETE /account` (#753)
  - [x] `workouts/upload` body-rakenne korjattu `{workout: {...}, date: ...}` (#754)
- [x] **Backend: Lisätty `GET /workouts/history`** – Puuttuva endpoint kalenterille (#755)
- [x] **Backend: `days_left` laskettu** – Viikoittaisen tavoitteen loppupäivä (ma–su) (#756)
- [x] **RangeError korjattu** – `profile_screen.dart` kaatui tyhjällä displayName-stringillä (#757)
  - [x] `displayName[0]` → `displayName.isNotEmpty ? displayName[0] : '?'` (#758)
- [x] **GoalFormSheet suojattu** – Dropdown RangeError jos backend-arvo ei listalla (#759)
- [x] **Race goal -näyttö korjattu** – `89.0 / 55.0 km` → `Race distance: 55.0 km` (#760)

### 17.3 Toteutusseuranta (Execution Score) ✅
Tavoite: Seurata noudattaako käyttäjä AI:n generoimaa ohjelmaa keston ja rasituksen osalta ja syöttää tämä takaisin AI:lle.

- [x] Backend: `firestore_manager.py` mäppää valmistuneet Garmin-aktiviteetit ("DONE") saman päivän AI-koutsauksiin ("PENDING") ja laskee 0-100 `execution_score`n. (#341)
- [x] Backend: `ai_coach.py` hakee viimeisen 7 päivän toteumat ja injektoi sen Gemini AI:n system promptiin. (#342)
- [x] Frontend: Mobiilisovelluksen `CalendarScreen`in kisakortit näyttävät nyt värillisen "Score: X%" -badgen riippuen onnistumisesta (Vihreä >80, Oranssi >50, Punainen <50). (#343)
- [x] **Status:** Coded and implemented directly following the user-approved implementation plan. (#344)

### 18.0 AI Valmentaja: XGBoost Ennusteet ✅
Tavoite: Syöttää koneoppimismallin (XGBoost) tuottama absoluuttinen matemaattinen palautumisennuste suoraan AI Valmentajan promptiin tarkan ja ennakoivan valmennuksen tueksi.
- [x] Backend: Uusi `backend/scripts/predict_readiness.py` -skripti joka lataa viimeisimmät (max 90 pv taaksepäin) tiedot ja laskee ennustetun arvon mallilla. (#345)
- [x] Backend: `predict_readiness.py` toteuttaa fallbackin lokaaliin globaaliin malliin jos käyttäjäkohtaista mallia ei löydy. (#346)
- [x] Backend: `main.py` injektoi tuloksen päivittäisen ja monipäiväisen `/plans/generate` tekoälyn promptiin. (#347)
- [x] Backend: `ai_coach.py` ottaa numeerisen ennusteen vastaan ja kieltää tehotreenit jos huomisen ennustettu `Body Battery` on alhainen (<45). (#348)
- [x] **Status:** Valmis ja testattu paikallisella cli-komennolla ja FastAPI palvelimen verifioinnilla. (#349)

### 18.1 MLflow Strategia (Päätös) 🛑
Tavoite: Linjata mallin elinkaaren hallinnan (MLOps) laajuus projektin tässä vaiheessa.
- [x] **Päätös:** MLflow pidetään toistaiseksi **vain lokaalina työkaluna** (SQLite + lokaalit tiedostot). Sitä käytetään vain mallikokeiluihin ja tutkimukseen omalla koneella. (#350)
- [x] **Perustelu:** Cloud Runissa raskaan taustaprosessin ylläpito ja levykirjoitukset ovat kalliita ja hitaita. Parhaat operatiiviset tulokset (metriikat ja mallin onnistuminen) viedään kevyesti suoraan Firestoreen. (#351)
- [x] **Linjaus:** Uusia Cloud-kytköksiä (Vertex AI, Cloud SQL for MLflow) ei rakenneta ennen kuin mallin monimutkaisuus tai tiimin koko sitä ehdottomasti vaatii. (#352)

---

## Phase 22: App Store Release & Tuotteistaminen (Mobile) ✅
> **Tavoite:** Android-mobiilisovelluksen brändäys, paketoiminen (.aab/.apk) ja suorajakelun (Sideloading) varmistaminen tuotantoympäristössä.
> **Status:** COMPLETED (2026-03-08)

### 22.1 Brändäys ja Visuaalisuus
- [x] **App Icon & Nimi:** Nimi päivitetty "Personal AI Coach" ja ikoni luotu "Tech Data" -teemalla (`flutter_launcher_icons`).
- [x] **Splash Screen:** Generoitu natiivit latausruudut `flutter_native_splash` -paketilla kaikkiin Android/iOS-kokoihin.

### 22.2 Tuotantoympäristö & API
- [x] **API Reititys:** Päivitetty `api_service.dart` käyttämään automaattisesti Cloud Run -tuotanto-osoitetta (`https://health-ai-backend-35976089058.europe-north1.run.app`) kun käännetään Release-moodissa (`kDebugMode`).

### 22.3 Julkaisu ja Turvallisuus (Keystore)
- [x] **Android Keystore:** Luotu `upload-keystore.jks` ja konfiguroitu `android/key.properties` salasanat `.gitignore`:n taakse.
- [x] **App Bundle (AAB):** Käännetty valmis `app-release.aab` Google Play Console -julkaisua varten.

### 22.4 Sideloading & Web Jakelu
- [x] **APK Suorajakelu:** Käännetty erillinen `app-release.apk` ja injektoitu Next.js -frontendin `public/`-kansioon.
- [x] **Web Landing Page:** Lisätty "Download for Android" -latauspainike, josta sovelluksen voi asentaa suoraan puhelimeen ilman kauppaa.

---

## Phase 23: Scalable Architecture & Data Sync Stability (2026-03-10) ✅

Tavoitteena vikasietoisuuden parantaminen ja skaalautuvuuden varmistaminen poistamalla riippuvuudet Firestore-indekseistä.

- [x] **Garmin Sync Fix (403 Forbidden):** (#900)
    - [x] Korjattu `display_name` käsittely ja sessioiden hallinta. Estetty `/None` -virheet API-pyynnöissä.
- [x] **Firestore Nested Architecture:** (#901)
    - [x] Siirretty `workouts`, `plans` ja `goals` käyttäjäkohtaisiksi subkokoelmiksi (`users/{uid}/workouts`).
    - [x] Poistettu tarve monimutkaisille Firestore-indekseille (Scalable).
- [x] **Dashboard Card Logic & Fallbacks:** (#902)
    - [x] Readiness-kortin fallback Body Batteryyn (estää `--%` näkymän).
    - [x] Weekly Load -kuvaajan daily breakdown -logiikka bäkendiin.
    - [x] Automaattinen kuormituksen laskenta Garmin-treeneille (duration-based fallback).
- [x] **ML Reliability Guardrails:** (#903)
    - [x] Lisätty miniminäytemäärä (5 päivää) XGBoost-koulutukselle.

---

## Phase 24: Mobile UI/UX & Data Logic Refinement (2026-03-12) 🛠️

Tavoitteena mobiilisovelluksen visuaalisten ja laskennallisten virheiden korjaus.

- [x] **Fitness & Fatigue Chart Scaling:** (#910)
    - [x] Korjaa Y-akselin etikettien päällekkäisyys mobiilissa.
- [x] **ML model Health (R² Score) Fix:** (#911)
    - [x] Tutki miksi R² score näyttää virheellisiä arvoja (-103%).
- [x] **Load & Duration Calculation:** (#912)
    - [x] Varmista kuormituslukujen oikeellisuus (2214 Load anomaly).
- [x] **Calendar & Workout UI:** (#913)
    - [x] Korjaa kalenterin vieritysongelma.
    - [x] Varmista, että generoidut treenit näkyvät heti kalenterissa ja niistä tulee "pallo" päivälle.
    - [x] Korjaa Workout-korttien sisällön näkyvyys.

---

## Phase 29: ML Model Health UI Fix (2026-03-15) ✅

Tavoitteena korjata harhaanjohtavat "Training..."-tilat ja negatiiviset tarkkuusluvut.

- [x] **UI Decoupling:** "Training..."-tila ei enää riipu R²-luvusta, vaan todellisesta taustatyön tilasta. (#920)
- [x] **R² Display Cap:** Negatiiviset R²-luvut näytetään 0.0% tasolla käyttöliittymässä hämmennyksen välttämiseksi. (#921)

---

## Phase 30: ML Data Quality & Filters (2026-03-15) ✅

Tavoitteena puhdistaa data epärealistisista nollapäivistä, jotka sotkevat AI:n oppimista.

- [x] **Zero-Value Filtering:** Automaattinen suodatus päiville, jolloin kello ei ole ollut kädessä (BB < 10, Stress = 0). (#930)
- [x] **Date Continuity Check:** AI oppii nyt vain peräkkäisistä päivistä. Jos datassa on tauko, oppiminen "nollautuu" saumattomasti. (#931)

---

## Phase 31: Peak Recovery Prediction Breakthrough (2026-03-15) ✅ 🚀

Tavoitteena nostaa mallin ennustekykyä vaihtamalla ennusteen kohdetta.

- [x] **Target Shift:** Ennustetaan huomisen maksimilatausta (Peak BB) pelkän latausmäärän sijaan. (#940)
- [x] **Accuracy Breakthrough:** R² tarkkuus nousi 0% -> **25%** (validi matemaattinen korrelaatio löytynyt). (#941)
- [x] **Feature Optimization:** Tämän päivän stressitaso (`averageStressLevel`) tunnistettu tärkeimmäksi ennustajaksi. (#942)

---

## Phase 32: Mobile UI Layout Refinement (2026-03-15) ✅

- [x] **Workout Detail Scroll Fix:** Lisätty `SingleChildScrollView` treenin lisätietoihin, mikä poisti "Bottom overflowed" -virheet. (#950)

---

## Phase 33: Garmin 2FA Stability (2026-03-16) ✅

> **Status:** COMPLETED

- [x] **2FA Session Refresh:** Korjaa Garmin MFA-istunnon automaattinen uusiminen taustalla. (#960)
- [x] **Proactive Notifications:** Ilmoita käyttäjälle proaktiivisesti, jos Garmin-yhteys vaatii uutta koodia. (#961)
- [x] **MFA UI Warnings (Mobile & Web):** Lisätty näkyvät varoitusbannerit dashboardiin, jos Garmin-yhteys vaatii huomiota. (#962, #963) (#358)

---

## Phase 34: Mobile App Distribution & Beta Testing
> **Status:** PLANNED

**Tavoite:** Android-mobiilisovelluksen sujuva ja automatisoitu jakelu testikäyttäjille käyttäen olemassa olevaa Firebase-infrastruktuuria.

- [ ] **Firebase App Distribution Setup:** (#359)
  - [ ] Ota Firebase App Distribution käyttöön Firebase Consolessa. (#360)
  - [ ] Luo "beta-testaajat" -ryhmä ja kutsu ensimmäiset testaajat sähköpostilla. (#361)
- [ ] **CI/CD Automatisointi (GitHub Actions):** (#362)
  - [ ] Valmistele Firebase CLI / Service Account konfiguraatio CI-putkea varten. (#363)
  - [ ] Laajenna olemassa olevaa GitHub Actionsia kääntämään Flutterista luotettavasti Release `.apk`. (#364)
  - [ ] Konfiguroi automaattinen puskeminen Firebaseen kera julkaisunuottien (Release Notes), kun `main`-haara päivittyy. (#365)
- [ ] **Testaajien Kokemus:** (#366)
  - [ ] Testaa kutsuprosessin sujuvuus ja asennus ei-teknisellä käyttäjällä (AppTester / selainlataus). (#367)

## Phase 18: Stability & Production Resilience (2026-03-26) ✅
> **Status:** COMPLETED (2026-03-26)

- [x] **Garmin 429 Rate Limit Mitigation:** (#900)
    - [x] **Concurrency Locking:** Added backend locks for both login (`garmin_connect`) and background sync (`execute_refresh_task`) to prevent redundant/simultaneous requests to Garmin.
    - [x] **Automated Cool-down:** Implemented a 15-minute in-memory throttling period in the backend following any 429 error from Garmin. The server now returns an immediate response with a remaining-time countdown to allow account recovery.
    - [x] **Error Messaging:** Refined messages to help users distinguish between Garmin-level rate limits and backend issues.
- [x] **Mobile App Resilience:** (#901)
    - [x] **Timeout Increase:** Bumped mobile API request timeout from 15 seconds to 60 seconds to support slow Garmin authentication and MFA flows.
- [x] **Backend Reliability:**
    - [x] Fixed a critical import order issue (`threading`/`time` initialization) that caused backend crashes during reload.

**Status:** 🟢 **STABLE** - Throttling and concurrency controls are active.

---

## Phase 36: Garmin Cloudflare Bypass (Universal Fix v4) (2026-04-12) ✅
> **Status:** COMPLETED (2026-04-12)

- [x] **Direct Android SSO Post:** Bypassed Cloudflare completely by impersonating GCM_ANDROID_DARK over curl_cffi to /portal/api/login.
- [x] **Custom OAuth1 Exchange:** Circumvented garth 0.2.x hardcoded sso/embed mismatch by injecting specific Android consumer endpoint.
- [x] **Tempdir Serialization:** Eliminated W251bGwsIG51bGxd base64 0.2.x corruption errors by enforcing OS-level .dump(tmpdir) serialization for Firestore storage.

---

## Phase 35: Garmin Connect 0.3.1 Migration & Resilience (2026-04-03) ✅
> **Status:** COMPLETED (2026-04-03)

- [x] **GarminConnect 0.3.1 Upgrade:** Migrated from `garth` to native token management in `garminconnect 0.3.1` (using `curl_cffi` for browser impersonation). (#970)
- [x] **Token Persistence Resilience:** Implemented robust token encryption/decryption handling. The system now automatically falls back to fresh login if tokens are corrupted or incompatible. (#971)
- [x] **Connectivity Fix:** Verified mobile app to local backend communication via IP `192.168.1.130`. Added debug middleware to confirm 2-way traffic. (#972)
- [ ] **Final Verification:** Pending Garmin SSO 429 rate-limit expiry. Scheduled for tomorrow morning. (#973)

**Next Steps:** Early morning sync or Session Injection fallback.


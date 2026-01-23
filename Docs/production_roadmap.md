# 🚀 Health AI: Production Scaling Roadmap (0 -> 10,000 Users)

Jos sovellus skaalattaisiin tuhansille käyttäjille, nykyinen "Local Single-User App" -arkkitehtuuri pitäisi muuttaa moderniksi pilviarkkitehtuuriksi.

## 1. Arkkitehtuuri & Backend (Cloud Native)
Nykyinen Streamlit + lokaali Python-skripti ei skaalaudu.
- [x] **Erota Frontend ja Backend:** Siirry pois monoliittisesta Streamlit-rakenteesta. (Aloitettu: Home View hakee datan API:sta) (#105)
- [x] **Backend-valinta:** Ota käyttöön FastAPI (Python) tai Node.js API:n rakentamiseen. (#106)
- [x] **API-suunnittelu:** Määrittele REST tai GraphQL rajapinta Fronendin käyttöön. (#107)
- [x] **Kontitus:** Paketoi sovellus Docker-konteiksi (Backend, Frontend). (#108)
- [ ] **Hosting:** Valmistele Cloud Run tai yksinkertainen VPS (Docker Compose) ympäristö. (Riittää sadoille käyttäjille) (#109)
- [ ] **Secrets:** Ota käyttöön Google Secret Manager API-avaimille ja service account -konfiguraatioille. (#110)

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
- [ ] **CI/CD Pipeline:** Laajenna GitHub Actions kattamaan automaattinen deploy (CD). (#171)
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
  - ✅ CI/CD Pipeline updated to run tests on push

### 7.4 Infrastructure Prep (Pre-deployment) 🚀
- [ ] **Secret Management:** Siirrä `service_account_key.json` → Google Secret Manager / .env (#240)
- [ ] **Environment Config:** Erota dev/staging/prod -ympäristöt (#241)
- [ ] **CI/CD Expansion:** (#242)
  - [ ] Lisää automaattinen deployment (CD) (#243)
  - [ ] **Docker image build ja push Container Registry:yn** (#244)

## 8. Admin Dashboard (Monitoring & Support) 🛠️
- [x] **Admin Authentication:** Implementoi "Admin Only" -tarkistus (esim. sallittujen sähköpostien lista backendissä). (#249)
- [x] **Dashboard UI:** Uusi sivu `/admin` (suojattu). (#250)
- [x] **Feedback Management:** Näytä käyttäjien palautteet (`GET /admin/feedback`). Mahdollisuus merkitä käsitellyksi. (#251)
- [ ] **User Overview:** Listaa käyttäjät ja heidän perustietonsa (auttaa debuggauksessa). (#252)

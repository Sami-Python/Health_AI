# 🚀 Health AI: Production Scaling Roadmap (0 -> 10,000 Users)

Jos sovellus skaalattaisiin tuhansille käyttäjille, nykyinen "Local Single-User App" -arkkitehtuuri pitäisi muuttaa moderniksi pilviarkkitehtuuriksi.

## 1. Arkkitehtuuri & Backend (Cloud Native)
Nykyinen Streamlit + lokaali Python-skripti ei skaalaudu.
- [x] **Erota Frontend ja Backend:** Siirry pois monoliittisesta Streamlit-rakenteesta. (Aloitettu: Home View hakee datan API:sta)
- [x] **Backend-valinta:** Ota käyttöön FastAPI (Python) tai Node.js API:n rakentamiseen.
- [x] **API-suunnittelu:** Määrittele REST tai GraphQL rajapinta Fronendin käyttöön.
- [x] **Kontitus:** Paketoi sovellus Docker-konteiksi (Backend, Frontend).
- [ ] **Hosting:** Valmistele Cloud Run tai yksinkertainen VPS (Docker Compose) ympäristö. (Riittää sadoille käyttäjille)
- [ ] **Secrets:** Ota käyttöön Google Secret Manager API-avaimille ja service account -konfiguraatioille.

## 2. Tietokanta (Multi-User & Scalability)
Nykyinen DuckDB/SQLite on tiedostopohjainen ja lukittuu usealla käyttäjällä.
- [x] **DB-migraatio:** Vaihda DuckDB -> Firestore. (Workouts & Goals & Plans migrated)
- [x] **Data Isolation:** Implementoi Row-Level Security (Firestore Rules) ja `user_id` jokaiseen dokumenttiin. (Toteutettu backendiin: `firestore_manager` filtteröi aina user_id:llä)
- [x] **Query Filtering:** Päivitä `firestore_manager.py` käyttämään `where('user_id', '==', uid)` -filtteriä kaikissa hauissa.
- [ ] **Legacy Migration (CRITICAL):** Siirrä Manual Workouts, Weekly Stats, ja Readiness -logiikka DuckDB:stä Firestoreen. (DuckDB ei tue user isolationia).

## 3. Käyttäjähallinta & Tietoturva (Security)
- [x] **Autentikaatio:** Ota käyttöön OAuth2 / OpenID Connect (Auth0, Firebase Auth).
- [x] **Backend Middleware:** Implementoi `main.py`:hyn middleware, joka verifioi Firebase ID -tokenin jokaisessa pyynnössä.
- [ ] **Kirjautuminen:** Toteuta Google/Apple/Email -kirjautumisvaihtoehdot.
- [ ] **Tietosuoja (GDPR):** Varmista datan salaus (At-Rest & In-Transit).
- [ ] **Data Encryption (GDPR):** Varmista datan salaus (At-Rest & In-Transit).
- [ ] **Datan hallinta:** Työkalu käyttäjän datan poistoon ("Oikeus tulla unohdetuksi").

## 3.5 Käyttäjäprofiili & Asetukset (User Management) 👤
- [ ] **Hamburger Menu:** Navigaatio oikeaan ylälaitaan (Settings, Profile, Logout).
- [ ] **Profile Page:**
    - [ ] Fysiologiset tiedot (Ikä, Paino, Pituus, Sukupuoli).
    - [ ] Sykerajat (Lepo- ja Maksimisyke).
- [ ] **Settings:**
    - [ ] Yksiköt (Metrinen/Imperial).
    - [ ] App Theme (Dark/Light).
    - [ ] AI Persona (Valmentajan tyyli).
- [ ] **Account Control:** Data Export & Delete Account.

## 4. AI & Mallit (LLM at Scale)
Nykyinen suora Gemini API -kutsu voi hidastua tai maksaa liikaa.
- [ ] **Mallien optimointi:** Vaihda kevyempään malliin (esim. Gemini Flash) rutiinitehtävissä.
- [ ] **Välimuisti (Caching):** Implementoi vastausten välimuisti samanlaisille kyselyille.
- [x] **Rate Limiting:** Rajoita API-kutsujen määrää per käyttäjä väärinkäytösten estämiseksi. (Toteutettu: slowapi)

## 5. Frontend (Käyttökokemus)
Streamlit on raskas tuhansille yhtäaikaisille käyttäjille.
- [x] **Moderni Web-kehys:** Rakenna käyttöliittymä Reactilla, Vuella tai Next.js:llä. (Toteutettu Next.js)
- [x] **Next.js Setup:** Alusta uusi Next.js -projekti (TypeScript, TailwindCSS) kansioon `web`.
- [x] **Frontend Features:** Training Calendar, Goals, Dashboard.
- [x] **Mobiilisovellus:** Web App toimii nyt mobiilissa (Responsive Design + Network Config).
- [ ] **Natiivi Mobiili (Optionaalinen):** Harkitse React Nativea tai Flutteria myöhemmin.
- [ ] **Flutter Setup:** Alusta uusi Flutter-projekti kansioon `mobile`.
- [ ] **Notifikaatiot:** Lisää Push-ilmoitukset (treenimuistutukset).
- [ ] **Integraatiot:** Kytke Apple Health / Google Fit -rajapintoihin.

## 5.5 Frontend Features (Next.js)
- [x] **Goal Management:** Mahdollisuus lisätä, muokata ja poistaa tavoitteita. (CRUD valmis: Backend & Frontend)
- [x] **Training Calendar:** Visuaalinen kuukausinäkymä, treenien tarkastelu (Modal), tulevat suunnitelmat.
- [ ] **Workout Logging:** Lomake treenien lisäämiseen.
- [ ] **UI Polish:** Moderni ilme (Dark Mode, Tailwind Components).

## 6. DevOps & Monitoring
- [ ] **CI/CD Pipeline:** Laajenna GitHub Actions kattamaan automaattinen deploy (CD).
- [ ] **Monitorointi:** Asenna Grafana/Datadog suorituskyvyn seurantaan.
- [ ] **Alerting:** Määritä hälytykset virhetilanteista (esim. API vastaa hitaasti).

---
### MVP -> Beta (Ensimmäiset askeleet)
- [-] Konfiguroi PostgreSQL-tietokanta. (SKIP)
- [x] Luo uusi FastAPI-projekti Backuiksi.
- [x] Integroi Firebase Auth.
- [ ] Konfiguroi Secret Manager.
- [x] Päivitä Firestore-haut tukemaan multi-user -mallia (user_id).
- [x] Alusta Next.js -projekti frontendille (web). (Kansio olemassa, mutta projekti on tyhjä scaffold)
- [x] Implementoi Frontendin perusrakenne (Authentication, API Client).
    - [x] Asenna kirjastot (Firebase SDK, Lucide Icons).
    - [x] Konfiguroi Firebase Client (web).
    - [x] Toteuta Login-sivu ja Auth Context.
    - [x] Testaa yhteys backendiin (Protected Route).
- [x] Implementoi "Add Goal" -toiminnallisuus (Create).
    - [x] Refined UI: Date Picker, Unit Dropdown, Frequency Logic.
- [ ] Tuo Dashboardin ulkoasu (CSS/Tailwind) samalle tasolle kuin Streamlit-versiossa.
- [ ] Alusta Flutter-projekti (mobile).
    - [x] Streamlit Migration: Feat Parity (History, Manual Logs, Refresh).
- [x] **Dashboard Visualizations (Phase 5)**:
    - [x] Backend: Historical Metrics Endpoint (Pandas/CSV).
    - [x] Implement Recovery Chart (Body Battery vs Sleep).
    - [x] Implement Load Chart (Daily Load).
    - [x] Implement Performance Chart (CTL/ATL/TSB) with Tooltips.
    - [x] Integrate Charts into Dashboard Grid.
- [x] **AI Insights (Phase 6)**:
    - [x] Backend: Add `GET /ai/insight` endpoint (Gemini API with Rate Limiting).
    - [x] Backend: Create `generate_daily_insight` prompt.
    - [x] Frontend: Implement `AIInsightCard` with gradient UI.
    - [x] Dependency: Added `google-generativeai`.

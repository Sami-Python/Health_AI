# Personal AI Coach

**Personal AI Coach** on älykäs, dataohjautuva valmennusjärjestelmä, joka auttaa optimoimaan palautumista ja harjoittelua.

Se yhdistää:
1.  **Garmin-datan** (uni, stressi, sykevariabiliteetti).
2.  **Machine Learning -mallin (XGBoost)**, joka ennustaa päivän vireystilan (Training Readiness / Body Battery).
3.  **Generatiivisen tekoälyn (Google Gemini)**, joka toimii henkilökohtaisena valmentajana ja luo päivittäiset treenisuositukset datan perusteella.

## Ominaisuudet
*   **Älykäs Dashboard:** Reaaliaikainen näkymä palautumisen tilasta ja treenihistoriasta.
*   **Treenikalenteri:** Visuaalinen yleisnäkymä (Kuukausi/Viikko), jossa erottuvat tehdyt ja suunnitellut treenit.
*   **Adaptiivinen AI Coach:** Valmentaja, joka huomioi väsymyksen ja luo uuden ohjelman yhdellä klikkauksella.
*   **Tavoitteellisuus:** Täysi hallinta tavoitteille (Lisää/Muokkaa/Poista) eri lajeissa (Juoksu, Hiihto, Pyöräily, etc.).
*   **Data & Analytiikka:** Kirjaa manuaaliset treenit ja seuraa "Suunniteltu vs Toteutunut" -kuormitusta viikkotasolla.
*   **Home View:** Keskitetty etusivu, joka näyttää heti palautumisen tilan ja seuraavan treenin.
*   **Tarkka Ennustemalli:** Omatuntoon perustuvaa arviota tarkempi koneoppimismalli vireystilan arviointiin.
*   **CI/CD Laatu:** Automaattiset yksikkötestit ja koodin laaduntarkistus (GitHub Actions).

## Teknologiat
*   **Frontend:** Next.js (React), TypeScript, Tailwind CSS
*   **Backend / AI:** Python, FastAPI, XGBoost, Google Gemini API
*   **Tietokanta:** DuckDB (Data Science), Firebase Firestore (App Data & Auth)
*   **Infra:** Docker

## Käynnistys (Local Development)

### 1. Backend (API)
```bash
# Vaihtoehto A: Docker (Suositus)
docker-compose up backend

# Vaihtoehto B: Manuaalisesti
cd backend
# Varmista virtuaaliympäristö
../.venv/Scripts/activate
uvicorn main:app --reload
```
API vastaa osoitteessa: `http://localhost:8000`

### 2. Frontend (Web App)
```bash
cd frontend
npm install # Ensimmäisellä kerralla
npm run dev
```
Sovellus on käytettävissä: `http://localhost:3000`

## Arkkitehtuuri
*   **Frontend:** Next.js - Moderni ja responsiivinen käyttöliittymä.
*   **Backend:** FastAPI - Tehokas rajapinta datan käsittelyyn ja AI-logiikkaan.
*   **Data Pipeline:** 
    *   `backend/scripts/`: Scriptit datan hakuun (Garmin) ja mallien koulutukseen.
    *   `backend/data/`: Paikalliset tietovarastot (`health_ai.db`).
*   **Firebase:**
    *   **Authentication:** Käyttäjien hallinta ja kirjautuminen.
    *   **Firestore:** Reaaliaikainen tietokanta käyttäjädatalle (tavoitteet, treenit).

## 📸 Screenshots

> **Note:** Screenshots coming soon! To see the app in action, run it locally (see [Käynnistys](#käynnistys-local-development)).

**Dashboard:**
- Recovery metrics and AI insights
- Goal tracking with progress bars
- Weekly training calendar

![Dashboard](Docs/pics/image-2.png)

**Goal Management:**
- Create recurring or race goals
- Track progress with visual indicators
- Edit and delete functionality

![Goal Management](Docs/pics/image-3.png)

**Training Calendar:**
- Month and week views
- Drag-and-drop workout planning
- Completed vs. planned workout visualization

![Training Calendar](Docs/pics/image-4.png)

**Profile & Settings:**
- Secure Garmin integration (AES-256 encrypted)
- User profile management
- GDPR-compliant data export

![Profile & Settings](Docs/pics/image-6.png)

**Model Accuracy:**
- XGBoost model performance metrics
- Training and validation accuracy
- Feature importance visualization

![Model Accuracy - Metrics](Docs/pics/image-5.png)
![Model Accuracy - Feature Importance](Docs/pics/image-7.png)

---

## 🔌 API Documentation

**Interactive API Docs (Swagger UI):**
```
http://localhost:8001/docs
```

**Full API Reference:** [Docs/API.md](Docs/API.md)

**Quick Example:**
```bash
# Get your goals
curl -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
     http://localhost:8001/goals
```

## 📚 Dokumentaatio

Lisää teknisiä yksityiskohtia ja arkkitehtuurikuvauksia löydät `Docs/`-kansiosta:

- **[API.md](Docs/API.md)** - Complete API reference, endpoints, examples
- **[authentication.md](Docs/authentication.md)** - Firebase Authentication toteutus, token flow, multi-user data isolation
- **[arkkitehtuuri.md](Docs/arkkitehtuuri.md)** - Järjestelmän arkkitehtuuri, komponentit ja datavirrat
- **[production_roadmap.md](Docs/production_roadmap.md)** - Kehityspolku 0 → 10,000 käyttäjää, skaalautuvuussuunnitelma
- **[sami_memo.md](Docs/sami_memo.md)** - Kehityspäiväkirja ja muutoshistoria
- **[garmin_setup.md](Docs/garmin_setup.md)** - Garmin credentials setup and troubleshooting


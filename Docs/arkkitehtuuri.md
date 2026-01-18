# Arkkitehtuuri - Sami's AI Coach

## Järjestelmän Yleiskuva
Sami's AI Coach on datalähtöinen valmennusjärjestelmä, joka yhdistää Garminin fysiologisen datan, koneoppimisen (XGBoost) ennustemallit ja generatiivisen tekoälyn (Gemini 2.5) tarjotakseen personoitua palautumisanalyysiä ja treenisuosituksia.

## Arkkitehtuurikaavio (Mermaid)

```mermaid
graph TD
    %% Ulkoiset Palvelut
    Garmin((Garmin Connect API))
    Gemini((Gemini 2.5 AI))
    User((Käyttäjä))

    %% Firebase Platform
    subgraph "Firebase Platform"
        FirebaseAuth[Authentication]
        Firestore[("Firestore DB<br/>Goals / Workouts / Plans<br/>Metrics / Insights")]
    end

    %% Data Ingestion Layer
    subgraph "Data Ingestion (Scripts)"
        Fetcher[fetch_garmin_data.py]
        Processor[process_garmin_data.py]
        CSV[("CSV Cache<br/>backend/data/<br/>(Garmin History)")]
    end

    %% Machine Learning Core
    subgraph "AI & ML Core"
        XGB_Model[XGBoost Model]
        Predictor[predict_readiness.py]
        CoachLogic[ai_coach.py]
    end

    %% Moderni Käyttöliittymä
    subgraph "Modern UI (Next.js)"
        UI_Login[Login / Auth]
        UI_Dashboard[Dashboard Page]
        UI_Charts["Recharts<br/>(Recovery, Load, Performance)"]
        UI_AICard[AI Insight Card]
    end

    %% Backend Services
    subgraph "Backend API"
        FastAPI[FastAPI Service]
    end

    %% Data Flow - External
    Garmin -->|JSON| Fetcher
    Fetcher -->|Tallentaa (Legacy)| CSV
    
    %% ML Flow
    CSV -.->|Opetusdata (Legacy)| Processor
    Firestore -->|Metrics History| Processor
    Processor -->|Kouluttaa| XGB_Model
    
    %% Backend Integration
    FastAPI -->|Lue Historia| Firestore
    FastAPI -->|Lue/Kirjoita| Firestore
    FastAPI -->|Trigger| Fetcher
    FastAPI -->|Generoi| CoachLogic
    
    CoachLogic -->|Prompt| Gemini
    
    %% UI Integration
    User -->|Kirjautuu| UI_Login
    UI_Login -.->|Token| FirebaseAuth
    
    User -->|Selaa| UI_Dashboard
    UI_Dashboard -->|Render| UI_Charts
    UI_Dashboard -->|Render| UI_AICard
    
    UI_Dashboard <-->|"API Calls (Bearer Token)"| FastAPI
    FastAPI -.->|Verify Token| FirebaseAuth

    %% CSV is now just a cache layer for Garmin historical data
    style CSV fill:#ffffcc,stroke:#ffaa00,stroke-dasharray: 2 2
```

![alt text](image-1.png)

## Komponentit

### 1. Moderni Käyttöliittymä (Next.js)
*   **Kehitysportaali (`frontend/`):** React-pohjainen sovellus, joka tarjoaa rikkaan käyttökokemuksen.
    *   **Dashboard:** Päänäkymä, joka kokoaa kaiken tiedon.
    *   **Goal Management:** Tavoitteiden hallinta (CRUD) ja Race-tavoitteet.
    *   **Training Calendar:** Interaktiivinen kalenteri (Drag & Drop) treenien suunnitteluun.
    *   **Recharts / Sparklines:** Interaktiiviset kuvaajat ja minitrendit korteissa.
    *   **AI Insight Card:** Päivittäinen yhteenveto tekoälyltä.
    *   **Authentication:** Firebase Auth -integraatio sisäänkirjautumiseen.
    *   **Toast Notifications:** Reaaliaikaiset käyttäjäilmoitukset (react-hot-toast) - success/error feedback kaikille toiminnoille.

### 2. Firebase Platform (Pilvipalvelut)
*   **Authentication:** Hallinnoi käyttäjien identiteettiä ja turvallisuutta (JWT).
    *   **Google Sign-In:** Käyttäjät kirjautuvat Google-tileillään
    *   **Token-Based Security:** Jokainen API-kutsu validoidaan Firebase ID Tokenilla
    *   **Multi-User Isolation:** Data eristetään automaattisesti `user_id`-perusteella
    *   📖 **Tekninen dokumentaatio:** [authentication.md](authentication.md)
*   **Firestore:** NoSQL-tietokanta, joka säilyttää:
    *   Käyttäjän tavoitteet (`goals`)
    *   Treenit (`workouts`)
    *   AI-suunnitelmat (`plans`)
    *   Profiilit (`users`)
    *   **Garmin Credentials:** Salatut Garmin-tunnukset (`users/{uid}/garmin_credentials/default`)
        *   **Encryption:** AES-256 (Fernet) - Salasanat luettavissa vain oikealla salausavaimella
        *   **Security:** Admin ei näe salasanoja ilman `ENCRYPTION_KEY`-avainta
        *   📖 **Setup Guide:** [garmin_setup.md](garmin_setup.md)

### 3. Backend & AI Core (Älykkyys)
*   **Backend API (`backend/`):** FastAPI-palvelin (v1.0.0), joka orkestroi liikenteen UI:n, tietokantojen ja AI-mallien välillä.
    *   **API Documentation:** Interaktiivinen Swagger UI (`/docs`)
    *   **Rate Limiting:** Endpoint-kohtaiset rajat (slowapi)
    *   **Authentication Middleware:** Firebase token verification
    *   📖 **API Reference:** [API.md](API.md)
*   **Backend Scripts (`backend/scripts/`):** Datan haku- ja käsittelyscriptit (ETL).
    *   **Per-User Garmin Fetch:** `fetch_garmin_data.py` tukee käyttäjäkohtaisia tunnuksia
*   **AI Coach (`backend/ai_coach.py`):** Yhdistää fysiologisen datan Gemini 2.5 -kielimalliin. **Sisältää välimuistin (Firestore Cache)** API-kiintiöiden hallintaan.
*   **Machine Learning:** XGBoost-mallit ennustavat tulevaa valmiustilaa (`readiness`) historian perusteella.

### 4. Data Layer (Tietovarasto)
*   **Firestore (Primary):** Pääasiallinen tietokanta kaikelle käyttäjädatalle (Goals, Workouts, Plans, User Profiles).
*   **CSV Cache (`backend/data/`):** Garmin-data haetaan CSV-muodossa ja käytetään ML-mallin koulutukseen. Toimii välimuistina historialliselle datalle.
*   **User Isolation:** Kaikki Firestore-kyselyt filtteröidään automaattisesti `user_id`:llä (Row-Level Security).


## Teknologia-stack
*   **Frontend:** Next.js 14, React, Recharts, Tailwind CSS
*   **Backend:** Python 3.10 (FastAPI), Pandas, XGBoost
*   **AI/ML:** Google Gemini 2.5 Flash, XGBoost Regressor
*   **Data:** Firestore (Primary), CSV (Garmin Cache)
*   **Infra:** Docker Compose

---

## 📖 Katso myös

- **[API.md](API.md)** - Complete API reference (25+ endpoints, examples, rate limits)
- **[authentication.md](authentication.md)** - Käyttäjien tunnistautuminen ja multi-user data isolation
- **[garmin_setup.md](garmin_setup.md)** - Garmin credentials encryption setup & troubleshooting
- **[production_roadmap.md](production_roadmap.md)** - Skaalautuvuussuunnitelma (0 → 10,000 käyttäjää)
- **[sami_memo.md](sami_memo.md)** - Kehityspäiväkirja ja projektin historia

---

**Last Updated:** 2026-01-18  
**API Version:** 1.0.0  
**Architecture Status:** Production Ready


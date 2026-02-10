# Arkkitehtuuri – Sami's AI Coach

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
        CSV[("CSV Cache<br/>backend/data/<br/>(ML Training Source)")]
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
        UI_Chat[AI Chat Widget]
    end

    %% Backend Services
    subgraph "Backend API"
        FastAPI[FastAPI Service]
        ChatManager[ai_chat_manager.py]
    end

    %% Data Flow - External
    Garmin -->|JSON| Fetcher
    Fetcher -->|Tallentaa (Cache)| CSV
    Fetcher -->|Synkronoi (Activities)| Firestore
    
    %% ML Flow
    CSV -->|Opetusdata| Processor
    Processor -->|Kouluttaa| XGB_Model
    Processor -->|Tallentaa (Metrics/Models)| Firestore
    
    %% Backend Integration
    FastAPI -->|Lue Historia/Metriikat| Firestore
    FastAPI -->|Lue/Kirjoita| Firestore
    FastAPI -->|Trigger| Fetcher
    FastAPI -->|Generoi| CoachLogic
    FastAPI -->|Keskustele| ChatManager
    
    CoachLogic -->|Prompt| Gemini
    ChatManager -->|Prompt| Gemini
    
    %% UI Integration
    User -->|Kirjautuu| UI_Login
    UI_Login -.->|Token| FirebaseAuth
    
    User -->|Selaa| UI_Dashboard
    UI_Dashboard -->|Render| UI_Charts
    UI_Dashboard -->|Render| UI_AICard
    UI_Dashboard -->|Render| UI_Chat
    
    UI_Dashboard <-->|"API Calls (Bearer Token)"| FastAPI
    FastAPI -.->|Verify Token| FirebaseAuth

    %% CSV is cache layer
    style CSV fill:#ffffcc,stroke:#ffaa00,stroke-dasharray: 2 2
```



## Komponentit

### 0. Public Landing Page (Cloudflare Pages)
*   **Landing Site (`landing_page/`):** Staattinen HTML/CSS -aloitussivu julkista markkinointia varten.
*   **Deployment:** Cloudflare Pages (globaali CDN, automaattinen SSL)
    *   **Live URL:** https://www.personalaicoach.ai

### 1. Moderni Käyttöliittymä (Next.js)
*   **Kehitysportaali (`frontend/`):** React-pohjainen sovellus, joka tarjoaa rikkaan käyttökokemuksen.
    *   **Dashboard:** Päänäkymä, joka kokoaa kaiken tiedon.
    *   **Goal Management:** Tavoitteiden hallinta (CRUD) ja Race-tavoitteet.
    *   **Training Calendar:** Interaktiivinen kalenteri (Drag & Drop).
    *   **AI Chat Coach:** Interaktiivinen chatti.
    *   **Authentication:** Firebase Auth -integraatio.
    *   **API Client:** Kommunikoi Backendin kanssa (`fetchWithRetry`).

### 2. Firebase Platform (Pilvipalvelut)
*   **Authentication:** Hallinnoi käyttäjien identiteettiä ja turvallisuutta (JWT).
*   **Firestore:** NoSQL-tietokanta (Source of Truth UI:lle):
    *   Käyttäjän tavoitteet, treenit, suunnitelmat, profiilit.
    *   **Garmin Metrics:** Prosessoidut metriikat (Daily Summary, Load, Stress).
    *   **Garmin Credentials:** Salatut tunnukset.

### 3. Backend & AI Core
*   **Backend API (`backend/`):** FastAPI-palvelin (v1.0.0).
    *   Orkestroi liikenteen ja validoi liikenteen (`firebase-admin`).
    *   **Huomio:** Käyttää sisäisesti `firestore_manager.py`:tä tietokantatoimintoihin.
*   **Backend Scripts (`backend/scripts/`):**
    *   `fetch_garmin_data.py`: Hakee datan Garminilta -> Tallentaa CSV (välimuisti) JA Synkronoi aktiviteetit Firestoreen.
    *   `process_garmin_data.py`: Lukee CSV-historian -> Kouluttaa XGBoost-mallin (Inkrementaalinen päivitys / Full retrain) -> Laskee metriikat (CTL/ATL/TSB) -> Tallentaa tulokset Firestoreen.
*   **AI Coach:** Yhdistää fysiologisen datan Gemini 2.5 -kielimalliin.

### 4. Data Layer (Tietovarasto)
*   **Firestore (Primary):** Pääasiallinen tietokanta kaikelle käyttöliittymässä näkyvälle datalle.
*   **CSV Cache (`backend/data/`):**
    *   Käytetään vain ML-mallin koulutukseen ja `process_garmin_data.py`:n syötteenä.
    *   Toimii varmuuskopiona ja "raw data" -kerroksena.

### 5. Configuration & DevOps
*   **Environment:** `backend/config.py` (Pydantic Settings).
*   **CI/CD:** GitHub Actions (Deploy to Cloud Run & Cloudflare Pages).
*   **Monitoring:** Google Cloud Logging / Error Reporting + Prometheus/Grafana stack.

### 6. MLOps
*   **MLflow:** Koemallien seuranta (`sqlite:///backend/data/mlflow.db`).
*   **Model Registry:** XGBoost-mallien versiointi ja feature importance -seuranta.

### 7. Observability
*   **Structured Logging:** JSON-muotoinen lokitus.
*   **Security Events:** Rate limit ja auth -virheiden auditointi.
